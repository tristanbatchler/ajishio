"""Multiplayerv2 chat server — binary packet protocol.

Assigns each connecting client a unique UUID, then relays Chat packets
to all connected clients.  Responds to Ping with Pong.
"""

import asyncio
from uuid import UUID, uuid4

import websockets
from websockets.asyncio.server import ServerConnection

from demo_projects.multiplayerv2.client.packets import (
    AssignId,
    Chat,
    ClientConnected,
    ClientDisconnected,
    Packet,
    Ping,
    Pong,
    decode,
)

HOST = "0.0.0.0"
PORT = 8765

_clients: dict[ServerConnection, UUID] = {}  # ws → sender_id


async def broadcast(message: str, *, exclude: ServerConnection | None = None) -> None:
    for ws in list(_clients):
        if ws is exclude:
            continue
        try:
            await ws.send(message)
        except Exception as exc:
            print(f"SERVER: broadcast error to {ws.remote_address}: {exc}")  # pyright: ignore[reportAny]


async def handle(ws: ServerConnection) -> None:
    sender_id = uuid4()
    _clients[ws] = sender_id

    addr = ws.remote_address  # pyright: ignore[reportAny]
    print(f"SERVER: connected {addr} as {sender_id.hex[:8]}, total={len(_clients)}")

    # First packet: tell the client its assigned ID.
    await ws.send(AssignId(sender_id=sender_id).encode())

    # Let everyone else know this client joined.
    await broadcast(ClientConnected(client_id=sender_id).encode(), exclude=ws)

    try:
        async for message in ws:
            if isinstance(message, bytes):
                message = message.decode("utf-8", "replace")

            pkt: Packet | None = decode(message.encode("utf-8"))
            if pkt is None:
                print(f"SERVER: malformed packet from {sender_id.hex[:8]}")
                continue

            if isinstance(pkt, Chat):
                print(f"SERVER: chat from {sender_id.hex[:8]}: {pkt.text!r}")
                # Re-encode with the server-verified sender_id and broadcast.
                out = Chat(sender_id=sender_id, text=pkt.text).encode()
                await broadcast(out)

            elif isinstance(pkt, Ping):
                print(f"SERVER: ping from {sender_id.hex[:8]} token={pkt.token}")
                await ws.send(Pong(token=pkt.token).encode())

            else:
                print(f"SERVER: unexpected packet type from {sender_id.hex[:8]}: {pkt}")

    except Exception as exc:
        print(f"SERVER: handler error: {exc}")
    finally:
        _ = _clients.pop(ws, None)
        print(f"SERVER: disconnected {sender_id.hex[:8]} {addr}, total={len(_clients)}")
        # Let everyone know this client left.
        await broadcast(ClientDisconnected(client_id=sender_id).encode())


async def main() -> None:
    async with websockets.serve(handle, HOST, PORT):
        print(f"chat server on {HOST}:{PORT}")
        await asyncio.Future()


asyncio.run(main())
