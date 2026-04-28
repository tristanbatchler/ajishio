import asyncio
import struct
import ajishio as aj
from typing import Unpack, override


def pack(text: str) -> bytes:
    body = text.encode("utf-8")
    raw = struct.pack("!BH", 1, len(body)) + body
    print("CLIENT pack:", raw, type(raw), len(raw))
    return raw


def unpack(data: bytes) -> str | None:
    print("CLIENT raw:", data, type(data), len(data))

    if len(data) < 3:
        return None

    tag, size = struct.unpack("!BH", data[:3])
    body = data[3:]

    print("CLIENT tag:", tag, "size:", size, "body:", body)

    if tag != 1 or len(body) != size:
        return None

    return body.decode("utf-8", "replace")


class NetTester(aj.GameObject):
    def __init__(self, client: aj.GameNetClient, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(0, 0, **kwargs)
        self.client = client
        self.sent = False
        self.lines: list[str] = []

    @override
    def step(self) -> None:
        super().step()

        if not self.sent:
            raw = pack("hello from ajishio client")
            print("CLIENT sending:", raw)
            self.client.send(raw)
            self.sent = True

        incoming = self.client.recv()
        while incoming is not None:
            print("CLIENT received raw from GameNetClient:", incoming, type(incoming))
            text = unpack(incoming)
            print("CLIENT decoded:", text)
            if text is not None:
                self.lines.append(text)
            incoming = self.client.recv()

    @override
    def draw(self) -> None:
        aj.draw_text(10, 10, "Binary GameNetClient test")
        for i, line in enumerate(self.lines[-10:]):
            aj.draw_text(10, 40 + i * 20, line)


async def main() -> None:
    client = aj.GameNetClient()
    await client.connect()

    _ = NetTester(client)

    await aj.async_game_start()


asyncio.run(main())
