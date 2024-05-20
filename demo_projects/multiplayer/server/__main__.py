from random import randrange
from uuid import UUID, uuid4
import socket
import demo_projects.multiplayer.shared.packet as pck
from dataclasses import dataclass
import threading
from queue import Queue
import ajishio as aj
from demo_projects.multiplayer.shared import rooms
import demo_projects.multiplayer.shared.game_objects as go


def send_packet(packet: pck.Packet, socket: socket.socket, address: tuple[str, int]) -> None:
    socket.sendto(packet.pack(), address)

@dataclass
class PlayerNetstate:
    obj: go.Player
    address: tuple[str, int]

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
 
    def broadcast(self, packet: pck.Packet, exclude: UUID) -> None:
        for player_id, player in self.players_netstates.items():
            if player_id != exclude:
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
        for player_id, player in self.players_netstates.items():
            send_packet(pck.PlayerPositionPacket(player.obj.x, player.obj.y), self.socket, player.address)

            self.broadcast(pck.OtherPlayerPositionPacket(player_id, player.obj.x, player.obj.y), exclude=player_id)

    def process_packets(self):
        while not self.packet_queue.empty():
            packet, address = self.packet_queue.get()
            if isinstance(packet, pck.ConnectionRequestPacket):
                self.handle_connection_request_packet(address)
            elif isinstance(packet, pck.PlayerXInputPacket):
                self.handle_player_x_input_packet(packet)
            elif isinstance(packet, pck.PlayerJumpPacket):
                self.handle_player_jump_packet(packet)
            elif isinstance(packet, pck.PlayerDisconnectPacket):
                self.handle_player_disconnect_packet(packet)

    def handle_connection_request_packet(self, address: tuple[str, int]) -> None:
        print('Connection from: ', address[0], ':', address[1]) 

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
            send_packet(pck.OtherPlayerPositionPacket(other_player_id, other_player.obj.x, other_player.obj.y), self.socket, address)

        # Send other players the new player's position
        self.broadcast(pck.OtherPlayerPositionPacket(player_id, player.x, player.y), exclude=player_id)

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
        self.broadcast(packet, exclude=packet.player_id)
        player_disconnecting: PlayerNetstate | None = self.players_netstates.pop(packet.player_id, None)
        if player_disconnecting is not None:
            aj.instance_destroy(player_disconnecting.obj)

if __name__ == '__main__':
    aj.set_rooms(rooms)
    aj.register_objects(go.Floor, GameServer, go.PlayerSpawner)
    aj.room_set_caption("Multiplayer Server")
    aj.window_set_size(960, 640)
    aj.room_set_background(aj.Color(155, 207, 239))
    aj.game_start()
    exit()
