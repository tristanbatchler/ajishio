import asyncio
import logging
from pathlib import Path
from typing import Unpack, override
import ajishio as aj

from string import ascii_lowercase, digits

from demo_projects.moonlapse.shared.packets import deserialize_from_server
import demo_projects.moonlapse.shared.packets.clientbound as clientbound
import demo_projects.moonlapse.shared.packets.serverbound as serverbound

# Printable characters we accept as input.
_TYPEABLE = ascii_lowercase + digits + " !?.,'-/"

HOST = "127.0.0.1"
PORT = 8766

log = logging.getLogger("moonlapse.client")


def _draw_wrapped_text(
    x: float,
    y: float,
    text: str,
    color: aj.Color,
    font: aj.Font,
    *,
    max_width: float = 0.0,
    line_height: float = 24.0,
) -> int:
    """Draw text wrapped to max_width. Returns number of lines drawn."""
    aj.draw_set_font(font)
    effective_max = max_width if max_width > 0 else aj.room_width - x - 20
    if effective_max <= 0:
        effective_max = aj.room_width - x - 20
    words = text.split()
    if not words:
        return 0
    lines: list[str] = []
    current_line: list[str] = []
    current_width: float = 0.0
    for word in words:
        word_w = aj.text_width(word) + aj.text_width(" ")
        if current_width + word_w > effective_max and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_w
        else:
            current_line.append(word)
            current_width += word_w
    if current_line:
        lines.append(" ".join(current_line))
    for i, line_text in enumerate(lines):
        aj.draw_text(x, y + i * line_height, line_text, color)
    return len(lines)


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
        self.logged_in: bool = False

    def log(self, message: str, color: aj.Color) -> None:
        self.message_log.append((message, color))
        log.info("%s", message)
        if len(self.message_log) > 50:
            self.message_log = self.message_log[-50:]

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
                if not pkt.ok:
                    self.log(f"Can't login: {pkt.err}", aj.c_orange)
                else:
                    self.logged_in = True
                    self.log("Login success", aj.c_lime)

            elif isinstance(pkt, clientbound.ClientId):
                self.my_id = pkt.id
                self.log(f"Obtained assigned ID: {self.my_id}", aj.c_aqua)

            elif isinstance(pkt, clientbound.LogoutResponse):
                if not pkt.ok:
                    self.log(f"Can't logout: {pkt.err}", aj.c_orange)
                else:
                    self.log("Logout success", aj.c_lime)

            elif isinstance(pkt, clientbound.ChatResponse):
                if not pkt.ok:
                    self.log(f"Can't send that: {pkt.err}", aj.c_orange)

            elif isinstance(pkt, clientbound.MoveResponse):
                if not pkt.ok:
                    self.log(f"Can't move there: {pkt.err}", aj.c_orange)
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
                self.log(pkt.message, aj.c_yellow)

            elif isinstance(pkt, clientbound.ClientDisconnected):
                self.log(f"Player {pkt.client_id} disconnected", aj.c_yellow)

            elif isinstance(pkt, clientbound.PlayerChat):
                self.log(
                    f"Player {pkt.from_client_id} says: '{pkt.message}'", aj.c_white
                )

            incoming = self.client.recv()

        # Text input
        for ch in _TYPEABLE:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_backspace) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if aj.keyboard_check_pressed(aj.vk_enter) and self.input_buffer.strip():
            raw = self.input_buffer.strip()

            # Command parser
            if raw.startswith("/"):
                parts = raw.split()
                cmd = parts[0]
                if cmd == "/login" and len(parts) >= 3:
                    login_pkt = serverbound.LoginRequest(
                        username=parts[1], password=parts[2]
                    )
                    self.client.send(login_pkt.serialize())
                    self.log(f"Sending login as {parts[1]}", aj.c_lime)
                elif cmd == "/who":
                    self.log(f"My ID: {self.my_id}", aj.c_aqua)
                else:
                    self.log(f"Unknown command: {cmd}", aj.c_red)
            else:
                pkt = serverbound.ChatRequest(self.input_buffer)
                self.client.send(pkt.serialize())

            self.input_buffer = ""

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_set_font(self.font)

        title = "Moonlapse"
        if self.logged_in:
            title += " (logged in)"
            color = aj.c_lime
        elif self.connected:
            title += " (connected)"
            color = aj.c_aqua
        else:
            title += " (connecting...)"
            color = aj.c_yellow
        aj.draw_text(10, 10, title, color)

        # Render visible messages with proper spacing based on wrapped line count
        max_msg_y = 50
        visible: list[tuple[str, aj.Color]] = self.message_log[-15:]
        for line, color in visible:
            num_lines = _draw_wrapped_text(
                10, max_msg_y, line, color, self.font, max_width=500
            )
            max_msg_y += num_lines * 24

        cursor = "|" if self.cursor_visible else " "
        aj.draw_text(10, 400, self.input_buffer + cursor)


async def main() -> None:
    client = aj.GameNetClient(f"ws://{HOST}:{PORT}")
    await client.connect()
    mgr = Manager(client=client)
    mgr.connected = True
    aj.register_objects(Manager)
    aj.add_object(mgr)

    aj.room_set_caption("Moonlapse Client")
    await aj.game_start_async()


if __name__ == "__main__":
    asyncio.run(main())
