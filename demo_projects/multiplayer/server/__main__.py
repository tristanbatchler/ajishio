from random import randrange
from uuid import UUID, uuid4
import socket
import demo_projects.multiplayer.shared.packet as pck
from dataclasses import dataclass
import threading
from queue import Queue
import ajishio as aj
import demo_projects.multiplayer.shared as shared
import demo_projects.multiplayer.shared.game_objects as go


def send_packet(packet: pck.Packet, socket: socket.socket, address: tuple[str, int]) -> None:
    socket.sendto(packet.pack(), address)


@dataclass
class PlayerNetstate:
    obj: go.Player
    address: tuple[str, int]
    requested_position_sync_timer: float = 0


class GameServer(aj.GameObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.packet_queue: Queue = Queue()

        print("Server started")

        self.players_netstates: dict[UUID, PlayerNetstate] = {}

        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

        self.running = True

        self.sync_timer: float = 0
        self.sync_timeout: float = 1

    def broadcast(self, packet: pck.Packet, exclude: UUID | None = None) -> None:
        for player_id, player in self.players_netstates.items():
            if not exclude or player_id != exclude:
                send_packet(packet, self.socket, player.address)

    def listen(self) -> None:
        self.socket.bind(("", 12345))
        while self.running:
            try:
                data, address = self.socket.recvfrom(1024)
            except ConnectionResetError:
                continue
            packet: pck.Packet = pck.unpack(data)
            self.packet_queue.put((packet, address))

    def step(self) -> None:
        super().step()

        if not self.running:
            return
        try:
            self.process_packets()
        except KeyboardInterrupt:
            self.stop()

        self.sync_timer += aj.delta_time
        if self.sync_timer >= self.sync_timeout:
            self.sync_timer = self.sync_timer % self.sync_timeout
            self.sync_positions()

    def stop(self) -> None:
        print("Server stopped")
        self.running = False
        self.listen_thread.join()
        self.socket.close()

    def sync_positions(self) -> None:
        # We ask each player to report their position. If  they don't respond in time, we assume
        # they've disconnected or are cheating, so we disconnect them. If they do respond with a
        # reasonably close position to ours, we let them keep that position and we update ours and
        # all other players' positions to match theirs. If they respond with a position that's too
        # far away from ours, we snap them back to our position.
        for player_id, ns in self.players_netstates.copy().items():
            if ns.requested_position_sync_timer >= 5:
                print("Player", ns.obj, "is not responding to sync requests!")
                self.handle_player_disconnect_packet(pck.PlayerDisconnectPacket(player_id))
                continue

            ns.requested_position_sync_timer += 1
            send_packet(pck.PositionSyncRequestPacket(), self.socket, ns.address)

    def process_packets(self) -> None:
        while not self.packet_queue.empty():
            packet, address = self.packet_queue.get()

            print("Received packet from", address)

            if isinstance(packet, pck.ConnectionRequestPacket):
                self.handle_connection_request_packet(address)
            elif isinstance(packet, pck.PlayerXInputPacket):
                self.handle_player_x_input_packet(packet)
            elif isinstance(packet, pck.PlayerJumpPacket):
                self.handle_player_jump_packet(packet)
            elif isinstance(packet, pck.PlayerDisconnectPacket):
                self.handle_player_disconnect_packet(packet)
            elif isinstance(packet, pck.PositionSyncResponsePacket):
                self.handle_position_sync_response_packet(packet)

    def handle_connection_request_packet(self, address: tuple[str, int]) -> None:
        print("Connection from: ", address[0], ":", address[1])

        num_player_spawners = aj.instance_count(go.PlayerSpawner)
        player_spawner = aj.instance_find(go.PlayerSpawner, randrange(num_player_spawners))
        assert player_spawner is not None

        player = go.Player(player_spawner.x, player_spawner.y)
        player_id = uuid4()

        # Send the connecting player their ID and initial position
        send_packet(pck.PlayerIdPacket(player_id), self.socket, address)
        send_packet(pck.PlayerPositionPacket(player.x, player.y), self.socket, address)

        # Also send the connecting player the positions of all other players
        for other_player_id, other_player in self.players_netstates.items():
            send_packet(
                pck.OtherPlayerPositionPacket(
                    other_player_id, other_player.obj.x, other_player.obj.y
                ),
                self.socket,
                address,
            )

        # Send other players the new player's position
        self.broadcast(
            pck.OtherPlayerPositionPacket(player_id, player.x, player.y),
            exclude=player_id,
        )

        # Finally, add the new player to the list of players
        player_netstate = PlayerNetstate(player, address)
        self.players_netstates[player_id] = player_netstate

    def handle_player_x_input_packet(self, packet: pck.PlayerXInputPacket) -> None:
        player = self.players_netstates[packet.player_id]
        player.obj.input_x = packet.x_input
        self.broadcast(packet, exclude=packet.player_id)

    def handle_player_jump_packet(self, packet: pck.PlayerJumpPacket) -> None:
        player = self.players_netstates[packet.player_id]
        player.obj.jump()
        self.broadcast(packet, exclude=packet.player_id)

    def handle_player_disconnect_packet(self, packet: pck.PlayerDisconnectPacket) -> None:
        self.broadcast(packet)
        player_disconnecting: PlayerNetstate | None = self.players_netstates.pop(
            packet.player_id, None
        )
        if player_disconnecting is not None:
            aj.instance_destroy(player_disconnecting.obj)

    def handle_position_sync_response_packet(self, packet: pck.PositionSyncResponsePacket) -> None:
        print("Received position sync response from", packet.player_id)
        player = self.players_netstates[packet.player_id]
        distance = aj.point_distance(player.obj.x, player.obj.y, packet.x, packet.y)
        if distance < 10:
            print(
                "Player",
                packet.player_id,
                "reports position only",
                distance,
                "units away - accepting!",
            )
            player.obj.x = packet.x
            player.obj.y = packet.y
            self.broadcast(
                pck.OtherPlayerPositionPacket(packet.player_id, packet.x, packet.y),
                exclude=packet.player_id,
            )
            player.requested_position_sync_timer = 0
        else:
            print(
                "Player",
                packet.player_id,
                "is cheating! They reported a position",
                distance,
                "units away! Snapping back!",
            )
            send_packet(
                pck.PlayerPositionPacket(player.obj.x, player.obj.y),
                self.socket,
                player.address,
            )


if __name__ == "__main__":
    aj.set_rooms(shared.rooms)
    aj.register_objects(go.Floor, GameServer, go.PlayerSpawner)
    aj.room_set_caption("Multiplayer Server")
    aj.room_width = shared.room_width
    aj.room_height = shared.room_height
    aj.window_set_size(aj.room_width * 2, aj.room_height * 2)
    aj.view_set_wport(aj.view_current, aj.room_width)
    aj.view_set_hport(aj.view_current, aj.room_height)
    aj.room_set_background(shared.room_background_color)
    aj.game_start()
    exit()
