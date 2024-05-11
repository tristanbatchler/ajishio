import ajishio as aj
from uuid import UUID
import socket
import threading
import demo_projects.multiplayer.game_objects as go
import demo_projects.multiplayer.packet as pck

class NetworkClient(aj.GameObject):
    def __init__(self) -> None:
        super().__init__()
        self.players: dict[UUID, go.Player] = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

        self.player_id: UUID | None = None
        self.player_x: float | None = None
        self.player_y: float | None = None
        self.player: go.Player | None = None

    def send(self, packet: pck.Packet) -> None:
        self.socket.sendto(packet.pack(), ("localhost", 12345))

    def receive(self) -> None:
        self.socket.bind(("localhost", 0))
        self.send(pck.ConnectionRequestPacket())
        while True:
            data = self.socket.recv(1024)
            packet = pck.unpack(data)
    
            if isinstance(packet, pck.PlayerIdPacket):
                self.player_id = packet.player_id
            elif isinstance(packet, pck.PlayerPositionPacket):
                self.player_x = packet.x
                self.player_y = packet.y

            if self.player is None and self.player_id is not None and self.player_x is not None and self.player_y is not None:
                self.player = go.Player(self.player_id, self.player_x, self.player_y)

    def step(self) -> None:
        super().step()

        x_input: int = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)
        y_input: int = aj.keyboard_check(aj.vk_down) - aj.keyboard_check(aj.vk_up)

        if self.player is not None and abs(x_input) + abs(y_input) > 0:
            self.player.move(x_input, y_input)
            self.send(pck.PlayerInputPacket(self.player_id, x_input, y_input))

aj.room_set_caption("Multiplayer")
NetworkClient()
aj.game_start()