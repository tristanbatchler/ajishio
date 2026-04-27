import asyncio
from string import ascii_lowercase, digits
from typing import Unpack, override

import ajishio as aj
from demo_projects.multiplayerv2.client.net import GameClient
from demo_projects.multiplayerv2.client.packets import ChatMessage

# Printable characters we accept as input.
# ord() matches pygame key codes for this range of ASCII.
_TYPEABLE = ascii_lowercase + digits + " !?.,'-"

_K_BACKSPACE = 8  # pygame.K_BACKSPACE


class Manager(aj.GameObject):
    def __init__(
        self,
        client: GameClient,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.client: GameClient = client
        self.message_log: list[str] = []
        self.input_buffer: str = ""

    @override
    def step(self) -> None:
        super().step()

        # Receive and decode incoming packets
        incoming = self.client.recv()
        if incoming:
            print(f"GOT A PACKET!!!!!: {incoming!r}")
            msg = ChatMessage.decode(incoming)
            if msg:
                self.message_log.append(msg.text)

        # Text input
        for ch in _TYPEABLE:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(_K_BACKSPACE) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if aj.keyboard_check_pressed(aj.vk_enter) and self.input_buffer.strip():
            self.client.send(ChatMessage(text=self.input_buffer).encode())
            self.input_buffer = ""

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_text(10, 10, "Chatroom — type and press Enter to send")
        aj.draw_text(10, 30, f"> {self.input_buffer}_")
        for i, line in enumerate(self.message_log[-10:]):
            aj.draw_text(10, 60 + i * 20, line)


async def main() -> None:
    client = GameClient()
    await client.connect()
    _ = Manager(client)
    await aj.async_game_start()


asyncio.run(main())
