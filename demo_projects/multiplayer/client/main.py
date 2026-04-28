from typing import Unpack, override
import asyncio
import ajishio as aj
from uuid import UUID
import demo_projects.multiplayer.shared.game_objects as go
import demo_projects.multiplayer.shared.packet as pck
import demo_projects.multiplayer.shared as shared
from queue import Queue


class NetworkClient(aj.GameObject):
    def __init__(
        self,
        client: aj.GameNetClient,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.client: aj.GameNetClient = client

        self.packet_queue: Queue[pck.Packet] = Queue()

        self.player_id: UUID | None = None
        self.player: go.Player | None = None

        self.others: dict[UUID, go.Player] = {}

        self.kicked: bool = False

        self.last_input_x: int = 0

        # Tell the server we want to connect
        self.send_packet(pck.ConnectionRequestPacket())

    def send_packet(self, packet: pck.Packet) -> None:
        self.client.send(packet.pack())

    def ingest_packets(self) -> None:
        incoming = self.client.recv()
        while incoming is not None:
            packet = pck.decode(incoming)
            if packet is not None:
                self.handle_packet(packet)
            incoming = self.client.recv()

    @override
    def step(self) -> None:
        super().step()

        self.ingest_packets()

        self.process_packets()

        if self.player_id is None or self.player is None:
            return

        x_input: int = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)

        if x_input != self.last_input_x:
            self.player.input_x = x_input

            self.send_packet(pck.PlayerXInputPacket(self.player_id, x_input))

        if aj.keyboard_check_pressed(aj.vk_space):
            self.player.jump()
            for _ in range(3):
                # It won't matter if the server receives the jump packet multiple times, since
                # on subsequent jumps, the player won't be on the ground so the jump won't be applied
                self.send_packet(pck.PlayerJumpPacket(self.player_id))

        self.last_input_x = x_input

    def process_packets(self) -> None:
        while not self.packet_queue.empty():
            packet = self.packet_queue.get()
            self.handle_packet(packet)

    def handle_packet(self, packet: pck.Packet) -> None:
        if isinstance(packet, pck.PlayerIdPacket):
            self.handle_player_id_packet(packet)
        elif isinstance(packet, pck.PlayerPositionPacket):
            self.handle_player_position_packet(packet)
        elif isinstance(packet, pck.OtherPlayerPositionPacket):
            self.handle_other_player_position_packet(packet)
        elif isinstance(packet, pck.PlayerXInputPacket):
            self.handle_player_x_input_packet(packet)
        elif isinstance(packet, pck.PlayerJumpPacket):
            self.handle_player_jump_packet(packet)
        elif isinstance(packet, pck.PlayerDisconnectPacket):
            self.handle_player_disconnect_packet(packet)
        elif isinstance(packet, pck.PositionSyncRequestPacket):
            self.handle_position_sync_request_packet()

    def handle_player_id_packet(self, packet: pck.PlayerIdPacket) -> None:
        self.player_id = packet.player_id

    def handle_player_position_packet(self, packet: pck.PlayerPositionPacket) -> None:
        if self.player is not None:
            self.player.x = packet.x
            self.player.y = packet.y
        else:
            self.player = go.Player(packet.x, packet.y)

            if self.player_id is not None:
                self.player.name = self.player_id.hex[:4]

    def handle_other_player_position_packet(self, packet: pck.OtherPlayerPositionPacket) -> None:
        if packet.player_id in self.others:
            self.others[packet.player_id].x = packet.x
            self.others[packet.player_id].y = packet.y
        else:
            self.others[packet.player_id] = go.Player(packet.x, packet.y)
            self.others[packet.player_id].name = packet.player_id.hex[:4]

    def handle_player_x_input_packet(self, packet: pck.PlayerXInputPacket) -> None:
        other_player: go.Player | None = self.others.get(packet.player_id)
        if other_player is not None:
            other_player.input_x = packet.x_input

    def handle_player_jump_packet(self, packet: pck.PlayerJumpPacket) -> None:
        other_player: go.Player | None = self.others.get(packet.player_id)
        if other_player is not None:
            other_player.jump()

    def handle_player_disconnect_packet(self, packet: pck.PlayerDisconnectPacket) -> None:
        print("Received player disconnect packet")
        if packet.player_id == self.player_id:
            self.kicked = True
            aj.game_end()
            return

        other_player: go.Player | None = self.others.pop(packet.player_id, None)
        if other_player is not None:
            aj.instance_destroy(other_player)

    def handle_position_sync_request_packet(self) -> None:
        if self.player is not None and self.player_id is not None:
            self.send_packet(
                pck.PositionSyncResponsePacket(self.player_id, self.player.x, self.player.y)
            )

    @override
    def on_game_end(self) -> None:
        if not self.kicked and self.player_id is not None:
            self.send_packet(pck.PlayerDisconnectPacket(self.player_id))


async def main() -> None:
    aj.set_rooms(shared.rooms)
    aj.register_objects(go.Floor, go.PlayerSpawner)
    client = aj.GameNetClient()
    await client.connect()
    _ = NetworkClient(client)
    aj.room_set_caption("Multiplayer Client")
    aj.room_set_size(shared.room_width, shared.room_height)
    aj.window_set_size(shared.room_width * 2, shared.room_height * 2)
    aj.view_set_wport(aj.view_current, shared.room_width)
    aj.view_set_hport(aj.view_current, shared.room_height)
    aj.room_set_background(shared.room_background_color)
    await aj.async_game_start()


if __name__ == "__main__":
    asyncio.run(main())
