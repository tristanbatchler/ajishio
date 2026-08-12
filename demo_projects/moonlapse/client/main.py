import asyncio
from pathlib import Path
from typing import Unpack, override
import ajishio as aj

from string import ascii_lowercase, digits

from demo_projects.moonlapse.shared.packets import deserialize_from_server
import demo_projects.moonlapse.shared.packets.clientbound as clientbound
import demo_projects.moonlapse.shared.packets.serverbound as serverbound

# Printable characters we accept as input.
_TYPEABLE = ascii_lowercase + digits + " !?.,'-"

HOST = "127.0.0.1"
PORT = 8766


class Manager(aj.GameObject):
    def __init__(
        self,
        client: aj.GameNetClient,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.client: aj.GameNetClient = client
        self.my_id: int | None = None
        self.message_log: list[tuple[str, aj.Color]] = []
        self.input_buffer: str = ""
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.5
        self.font: aj.Font = aj.load_font(
            Path(__file__).parent / "CutiveMono-Regular.ttf", 24
        )
        self.connected: bool = False

    def log(self, message: str, color: aj.Color) -> None:
        self.message_log.append((message, color))
        print(message)

    @override
    def step(self) -> None:
        super().step()

        self.cursor_timer -= aj.delta_time
        if self.cursor_timer <= 0:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.5

        # Drain incoming packets (non-blocking, like multiplayerv2)
        incoming = self.client.recv()
        while incoming is not None:
            pkt = deserialize_from_server(incoming)

            if isinstance(pkt, clientbound.LoginResponse):
                self.connected = True
                if not pkt.ok:
                    self.log(f"Can't login: {pkt.err}", aj.c_orange)
                else:
                    self.log("Login success", aj.c_lime)

            elif isinstance(pkt, clientbound.ClientId):
                self.my_id = pkt.id
                self.message_log.append(
                    (f"Obtained assigned ID: {self.my_id}", aj.c_aqua)
                )

            elif isinstance(pkt, clientbound.LogoutResponse):
                if not pkt.ok:
                    self.log(f"Can't logout: {pkt.err}", aj.c_orange)
                else:
                    self.log("Logout success", aj.c_lime)

            elif isinstance(pkt, clientbound.ChatResponse):
                if not pkt.ok:
                    self.message_log.append(
                        (f"Can't send that: {pkt.err}", aj.c_orange)
                    )

            elif isinstance(pkt, clientbound.MoveResponse):
                if not pkt.ok:
                    self.message_log.append(
                        (f"Can't move there: {pkt.err}", aj.c_orange)
                    )
                else:
                    self.log("Move successful", aj.c_lime)

            elif isinstance(pkt, clientbound.RegisterResponse):
                if not pkt.ok:
                    self.log(f"Can't register: {pkt.err}", aj.c_orange)
                else:
                    self.log("Register success", aj.c_lime)

            elif isinstance(pkt, clientbound.Motd):
                self.log(pkt.motd, aj.c_aqua)

            elif isinstance(pkt, clientbound.Announcement):
                self.log(f"{pkt.message}", aj.c_yellow)

            elif isinstance(pkt, clientbound.ClientDisconnected):
                self.message_log.append(
                    (f"Player {pkt.client_id} disconnected", aj.c_yellow)
                )

            incoming = self.client.recv()

        # Text input
        for ch in _TYPEABLE:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_backspace) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if aj.keyboard_check_pressed(aj.vk_enter) and self.input_buffer.strip():
            pkt = serverbound.ChatRequest(self.input_buffer)
            self.client.send(pkt.serialize())
            self.input_buffer = ""

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_set_font(self.font)

        title = "Moonlapse"
        if self.connected:
            title += " (connected)"
        else:
            title += " (connecting...)"
        aj.draw_text(10, 10, title, aj.c_lime if self.connected else aj.c_yellow)

        for i, (line, color) in enumerate(self.message_log[-10:]):
            aj.draw_text(10, 50 + i * 30, line, color)

        cursor = "|" if self.cursor_visible else " "
        aj.draw_text(10, 400, self.input_buffer + cursor)


async def main() -> None:
    client = aj.GameNetClient(f"ws://{HOST}:{PORT}")
    await client.connect()
    mgr = Manager(client=client)
    aj.register_objects(Manager)
    aj.add_object(mgr)

    aj.room_set_caption("Moonlapse Client")
    await aj.game_start_async()


if __name__ == "__main__":
    asyncio.run(main())
