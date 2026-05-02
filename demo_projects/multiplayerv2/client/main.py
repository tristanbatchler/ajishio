import asyncio
import time
from random import randint
from string import ascii_lowercase, digits
from typing import Unpack, override
from uuid import UUID

import ajishio as aj
from demo_projects.multiplayerv2.shared.packets import (
    AssignId,
    Chat,
    ClientConnected,
    ClientDisconnected,
    Ping,
    Pong,
    decode,
)
from pathlib import Path

# Printable characters we accept as input.
# ord() matches pygame key codes for this range of ASCII.
_TYPEABLE = ascii_lowercase + digits + " !?.,'-"


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
        self.message_log: list[tuple[str, aj.Color]] = []
        self.input_buffer: str = ""
        self.cursor_visible: bool = True
        self.cursor_blink_interval: float = 0.5
        self.cursor_timer: float = self.cursor_blink_interval
        self.font: aj.Font = aj.load_font(Path(__file__).parent / "CutiveMono-Regular.ttf", 24)

        # Assigned by the server via AssignId packet.
        self.my_id: UUID | None = None

        # Ping bookkeeping — we store the wall-clock time locally and use a
        # random 32-bit token to match the Pong response.
        self._ping_token: int | None = None
        self._ping_sent_at: float = 0.0

    @override
    def step(self) -> None:
        super().step()

        self.cursor_timer -= aj.delta_time
        if self.cursor_timer <= 0:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer += self.cursor_blink_interval

        # ------------------------------------------------------------------
        # Receive and decode incoming packets
        # ------------------------------------------------------------------
        incoming = self.client.recv()
        while incoming is not None:
            pkt = decode(incoming)

            if isinstance(pkt, AssignId):
                self.my_id = pkt.sender_id
                short = self.my_id.hex[:8]
                self.message_log.append((f"* connected as {short}", aj.c_lime))
                # Send a ping now that we have an ID.
                self._ping_token = randint(0, 0xFFFFFFFF)
                self._ping_sent_at = time.monotonic()
                self.client.send(
                    Ping(
                        sender_id=self.my_id,
                        token=self._ping_token,
                    ).encode()
                )

            elif isinstance(pkt, Chat):
                short = pkt.sender_id.hex[:8]
                is_me = self.my_id is not None and pkt.sender_id == self.my_id
                color = aj.c_aqua if is_me else aj.c_white
                self.message_log.append((f"[{short}] {pkt.text}", color))

            elif isinstance(pkt, Pong):
                if self._ping_token is not None and pkt.token == self._ping_token:
                    rtt_ms = (time.monotonic() - self._ping_sent_at) * 1000
                    self.message_log.append((f"* pong: {rtt_ms:.0f} ms", aj.c_gray))
                    self._ping_token = None

            elif isinstance(pkt, ClientConnected):
                short = pkt.client_id.hex[:8]
                self.message_log.append((f"+ {short} joined", aj.c_lime))

            elif isinstance(pkt, ClientDisconnected):
                short = pkt.client_id.hex[:8]
                self.message_log.append((f"- {short} left", aj.c_orange))

            incoming = self.client.recv()

        # ------------------------------------------------------------------
        # Text input
        # ------------------------------------------------------------------
        for ch in _TYPEABLE:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_backspace) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if (
            aj.keyboard_check_pressed(aj.vk_enter)
            and self.input_buffer.strip()
            and self.my_id is not None
        ):
            self.client.send(Chat(sender_id=self.my_id, text=self.input_buffer).encode())
            self.input_buffer = ""

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_set_font(self.font)

        title = "Ajishio Chat Demo"
        if self.my_id is not None:
            title += f"  ({self.my_id.hex[:8]})"
            aj.draw_text(10, 10, title, aj.c_lime)
        else:
            title += "  (connecting...)"
            aj.draw_text(10, 10, title, aj.c_yellow)

        cursor = "|" if self.cursor_visible else " "
        font_height = aj.text_height("A") * 1.2
        max_messages = 10
        for i, (line, color) in enumerate(self.message_log[-max_messages:]):
            aj.draw_text(10, 10 + (i + 1) * font_height, line, color)

        aj.draw_text(10, 10 + (max_messages + 1) * font_height, self.input_buffer + cursor)


async def main() -> None:
    client = aj.GameNetClient("wss://ajishio.tbat.me/multiplayerv2")
    await client.connect()
    _ = Manager(client)
    # aj.room_set_caption("Multiplayer Client")
    await aj.game_start_async()


asyncio.run(main())
