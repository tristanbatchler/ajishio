import asyncio
import struct
import websockets
from websockets.asyncio.server import ServerConnection

HOST = "0.0.0.0"
PORT = 8765


def pack(text: str) -> bytes:
    body = text.encode("utf-8")
    return struct.pack("!BH", 1, len(body)) + body


def unpack(data: bytes) -> str | None:
    print("SERVER raw:", data, type(data), len(data))

    if len(data) < 3:
        return None

    tag, size = struct.unpack("!BH", data[:3])
    body = data[3:]

    print("SERVER tag:", tag, "size:", size, "body:", body)

    if tag != 1 or len(body) != size:
        return None

    return body.decode("utf-8", "replace")


async def handle(ws: ServerConnection) -> None:
    print("SERVER connected:", ws.remote_address)

    await ws.send(pack("welcome from binary server"))

    async for message in ws:
        print("SERVER incoming:", message, type(message))

        raw = message if isinstance(message, bytes) else message.encode("utf-8")
        text = unpack(raw)

        print("SERVER decoded:", text)

        if text is not None:
            await ws.send(pack(f"echo: {text}"))


async def main() -> None:
    async with websockets.serve(handle, HOST, PORT):
        print(f"SERVER listening on ws://{HOST}:{PORT}")
        await asyncio.Future()


asyncio.run(main())
