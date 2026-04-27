from pygame.font import Font


import asyncio
from string import ascii_lowercase, digits
from typing import Unpack, override

import ajishio as aj
from demo_projects.multiplayerv2.client.packets import ChatMessage
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
        self.message_log: list[str] = []
        self.input_buffer: str = ""
        self.cursor_visible: bool = True
        self.cursor_blink_interval: float = 0.5
        self.cursor_timer: float = self.cursor_blink_interval
        self.font: Font = aj.load_font(Path(__file__).parent / "CutiveMono-Regular.ttf", 24)

    @override
    def step(self) -> None:
        super().step()

        self.cursor_timer -= aj.delta_time
        if self.cursor_timer <= 0:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer += self.cursor_blink_interval

        # Receive and decode incoming packets
        incoming = self.client.recv()
        if incoming:
            msg = ChatMessage.decode(incoming)
            if msg:
                self.message_log.append(msg.text)

        # Text input
        for ch in _TYPEABLE:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_backspace) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if aj.keyboard_check_pressed(aj.vk_enter) and self.input_buffer.strip():
            self.client.send(ChatMessage(text=self.input_buffer).encode())
            self.input_buffer = ""

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_set_font(self.font)
        aj.draw_text(10, 10, "Ajishio Chat Demo", aj.c_lime)
        cursor = "|" if self.cursor_visible else " "
        font_height = aj.text_height("A") * 1.2
        max_messages = 10
        for i, line in enumerate(self.message_log[-max_messages:]):
            aj.draw_text(10, 10 + (i + 1) * font_height, line)

        aj.draw_text(10, 10 + (max_messages + 1) * font_height, self.input_buffer + cursor)


async def main() -> None:
    client = aj.GameNetClient()
    await client.connect()
    _ = Manager(client)
    await aj.async_game_start()


asyncio.run(main())
