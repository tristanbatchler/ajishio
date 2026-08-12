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
        self.font: aj.Font = aj.load_font(Path(__file__).parent / "CutiveMono-Regular.ttf", 24)
        self.connected: bool = False

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
                self.my_id = 1
                self.message_log.append(("* connected", aj.c_lime))

            elif isinstance(pkt, clientbound.LogoutResponse):
                self.message_log.append((f"* {'ok' if pkt.ok else pkt.err}", aj.c_orange))

            elif isinstance(pkt, clientbound.ChatResponse):
                self.message_log.append((f"  server: ok={pkt.ok}", aj.c_aqua))

            elif isinstance(pkt, clientbound.MoveResponse):
                self.message_log.append((f"  server: ok={pkt.ok}", aj.c_aqua))

            elif isinstance(pkt, clientbound.RegisterResponse):
                self.message_log.append((f"  server: ok={pkt.ok}", aj.c_aqua))

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
