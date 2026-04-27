import asyncio

import websockets
from websockets.asyncio.server import ServerConnection

HOST = "0.0.0.0"
PORT = 8765

_clients: set[ServerConnection] = set()


async def broadcast(message: str) -> None:
    for ws in list(_clients):
        try:
            await ws.send(message)
        except Exception as exc:
            print(f"SERVER: broadcast error to {ws.remote_address}: {exc}")  # pyright: ignore[reportAny]


async def handle(ws: ServerConnection) -> None:
    _clients.add(ws)
    addr = ws.remote_address  # pyright: ignore[reportAny]
    print(f"SERVER: connected {addr}, total={len(_clients)}")
    try:
        async for message in ws:
            if isinstance(message, bytes):
                message = message.decode("utf-8", "replace")
            print(f"SERVER: recv from {addr}: {message!r}")
            await broadcast(message)
    except Exception as exc:
        print(f"SERVER: handler error: {exc}")
    finally:
        _clients.discard(ws)
        print(f"SERVER: disconnected {addr}, total={len(_clients)}")


async def main() -> None:
    async with websockets.serve(handle, HOST, PORT):
        print(f"chat server on {HOST}:{PORT}")
        await asyncio.Future()


asyncio.run(main())
