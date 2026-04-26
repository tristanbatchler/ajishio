import asyncio
from string import ascii_letters
import ajishio as aj
from typing import Unpack, override

from demo_projects.multiplayerv2.client.net import GameClient


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
        self.keepalive_interval: float = 5.0
        self.keepalive_timer: float = self.keepalive_interval

    @override
    def step(self) -> None:
        super().step()

        incoming = self.client.recv()
        if incoming:
            self.message_log.append(f"Server: {incoming.decode()}")

        for ch in ascii_letters:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_enter):
            self.message_log.append(f"You: {self.input_buffer}")
            self.client.send({"t": "message", "text": self.input_buffer})
            self.input_buffer = ""

        self.keepalive_timer -= aj.delta_time
        if self.keepalive_timer <= 0:
            self.client.send_ping()
            self.keepalive_timer = self.keepalive_interval

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_text(10, 10, "Type something and press Enter to send it to the server.")
        aj.draw_text(10, 30, f"Input: {self.input_buffer}")
        for i, msg in enumerate(self.message_log[-10:]):
            aj.draw_text(10, 50 + i * 20, msg)


async def main():
    client = GameClient(nick="Player1")
    await client.connect()

    _ = Manager(client)

    await aj.async_game_start()


asyncio.run(main())
