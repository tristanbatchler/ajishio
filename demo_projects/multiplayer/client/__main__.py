import ajishio as aj
from uuid import UUID
import socket
import threading
import demo_projects.multiplayer.shared.game_objects as go
import demo_projects.multiplayer.shared.packet as pck
from demo_projects.multiplayer.shared import rooms
from queue import Queue

class NetworkClient(aj.GameObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("localhost", 0))

        self.packet_queue: Queue = Queue()

        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

        self.player_id: UUID | None = None
        self.player: go.Player | None = None
        self.others: dict[UUID, go.Player] = {}

        self.last_input_x: int = 0

        # Tell the server we want to connect
        self.send(pck.ConnectionRequestPacket())

    def send(self, packet: pck.Packet) -> None:
        self.socket.sendto(packet.pack(), ("localhost", 12345))

    def listen(self) -> None:
        while True:
            try:
                data = self.socket.recv(1024)
            except ConnectionResetError:
                print("Connection reset")
                aj.game_end()
                return
            
            except OSError as e:
                print("Got an error:", e)
                return

            packet = pck.unpack(data)
            self.packet_queue.put(packet)

    def step(self) -> None:
        super().step()

        self.process_packets()

        if self.player_id is None or self.player is None:
            return
    
        x_input: int = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)
        
        if x_input != self.last_input_x:
            self.player.input_x = x_input

            # For redundancy, send the change in input a few times and hope it gets through
            for _ in range(3):
                self.send(pck.PlayerXInputPacket(self.player_id, x_input))

        if aj.keyboard_check_pressed(aj.vk_space):
            self.player.jump()
            for _ in range(3):
                # It won't matter if the server receives the jump packet multiple times, since 
                # on subsequent jumps, the player won't be on the ground so the jump won't be applied
                self.send(pck.PlayerJumpPacket(self.player_id))

        self.last_input_x = x_input

    def draw(self) -> None:
        if self.player is None:
            return
        aj.draw_text(10, 10, f"({self.player.x}, {self.player.y})", aj.Color(0, 0, 0))

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

    def handle_player_id_packet(self, packet: pck.PlayerIdPacket) -> None:
        self.player_id = packet.player_id

    def handle_player_position_packet(self, packet: pck.PlayerPositionPacket) -> None:
        if self.player is not None:
            self.player.x = packet.x
            self.player.y = packet.y
        else:
            self.player = go.Player(packet.x, packet.y)

    def handle_other_player_position_packet(self, packet: pck.OtherPlayerPositionPacket) -> None:
        if packet.player_id in self.others:
            self.others[packet.player_id].x = packet.x
            self.others[packet.player_id].y = packet.y
        else:
            self.others[packet.player_id] = go.Player(packet.x, packet.y)

    def handle_player_x_input_packet(self, packet: pck.PlayerXInputPacket) -> None:
        other_player: go.Player | None = self.others.get(packet.player_id)
        if other_player is not None:
            other_player.input_x = packet.x_input

    def handle_player_jump_packet(self, packet: pck.PlayerJumpPacket) -> None:
        other_player: go.Player | None = self.others.get(packet.player_id)
        if other_player is not None:
            other_player.jump()

    def handle_player_disconnect_packet(self, packet: pck.PlayerDisconnectPacket) -> None:
        other_player: go.Player | None = self.others.pop(packet.player_id, None)
        if other_player is not None:
            aj.instance_destroy(other_player)

    def on_game_end(self) -> None:
        if self.player_id is not None:
            self.send(pck.PlayerDisconnectPacket(self.player_id))
        self.socket.close()

if __name__ == '__main__':
    aj.set_rooms(rooms)
    aj.register_objects(go.Floor, NetworkClient)
    aj.room_set_caption("Multiplayer Client")
    aj.window_set_size(960, 640)
    aj.room_set_background(aj.Color(155, 207, 239))
    aj.game_start()
    exit()
