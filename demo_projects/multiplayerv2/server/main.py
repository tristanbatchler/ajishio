import asyncio
import json
from typing import cast

import websockets
from websockets.asyncio.server import ServerConnection

HOST = "0.0.0.0"
PORT = 8765

type JSONValue = str | int | float | bool | None | dict[str, JSONValue] | list[JSONValue]
JSON = dict[str, JSONValue]


def pack(msg: JSON) -> str:
    return json.dumps(msg)


async def handle(ws: ServerConnection) -> None:
    addr = ws.remote_address  # pyright: ignore[reportAny]
    print("SERVER DEBUG: connected", addr)  # pyright: ignore[reportAny]

    try:
        await ws.send(pack({"t": "welcome", "message": "Welcome to the echo server!"}))
        print("SERVER DEBUG: sent welcome")

        async for message in ws:
            print("SERVER DEBUG: raw incoming message type=", type(message), "value=", message)
            try:
                msg = cast(JSON, json.loads(message))
            except Exception as exc:
                print("SERVER DEBUG: message parse failed", exc)
                await ws.send(pack({"t": "error", "message": "invalid json"}))
                continue

            print("SERVER DEBUG: recv", msg)
            try:
                await ws.send(pack({"t": "echo", "data": msg}))
                print("SERVER DEBUG: echoed message")
            except Exception as exc:
                print("SERVER DEBUG: send failed", exc)
                raise
    except Exception as exc:
        print("SERVER DEBUG: handler exception", exc)
        raise
    finally:
        print("SERVER DEBUG: disconnected", addr)  # pyright: ignore[reportAny]


async def main():
    async with websockets.serve(handle, HOST, PORT):
        print(f"websocket server on {HOST}:{PORT}")
        await asyncio.Future()


asyncio.run(main())
