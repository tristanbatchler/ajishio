from __future__ import annotations

import asyncio
from collections.abc import Collection
import logging
from websockets.asyncio.server import ServerConnection, serve

from demo_projects.moonlapse.shared.packets import deserialize_from_client
import demo_projects.moonlapse.shared.packets.serverbound as serverbound
import demo_projects.moonlapse.shared.packets.clientbound as clientbound

log = logging.getLogger("moonlapse")

HOST = "0.0.0.0"
PORT = 8766


class ClientSession:
    """Tracks a single connected client."""

    def __init__(self, client_id: int, ws: ServerConnection) -> None:
        self.client_id: int = client_id
        self.ws: ServerConnection = ws


class Hub:
    """Server-side state — accessed concurrently by WebSocket handlers."""

    def __init__(self) -> None:
        self._next_id: int = 1
        self._clients: dict[int, ClientSession] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def next_id(self) -> int:
        cid = self._next_id
        self._next_id += 1
        return cid

    def register_client(self, client_id: int, session: ClientSession) -> None:
        self._clients[client_id] = session

    def unregister_client(self, client_id: int) -> ClientSession | None:
        for ws, sess in self._clients.items():
            if sess.client_id == client_id:
                del self._clients[ws]
                return sess
        return None

    def get_clients(self) -> Collection[ClientSession]:
        return self._clients.values()

    async def send_to(
        self, client_id: int, packet: clientbound.ClientboundPacket
    ) -> None:
        for sess in self._clients.values():
            if sess.client_id == client_id:
                try:
                    await sess.ws.send(packet.serialize())
                except Exception as exc:
                    log.warning("send_to %d failed: %s", client_id, exc)
                return

    async def broadcast(self, packet: clientbound.ClientboundPacket) -> None:
        for cid, session in self._clients.items():
            try:
                await session.ws.send(packet.serialize())
            except Exception as exc:
                log.warning(f"broadcast failed to {cid}: {exc}")


async def _handle_client(hub: Hub, ws: ServerConnection) -> None:
    cid = hub.next_id
    session = ClientSession(cid, ws)
    hub.register_client(cid, session)

    log.info(f"connected {cid} as {ws.remote_address}, total={len(hub.get_clients())}")  # pyright: ignore[reportAny]

    # Assign ID + notify
    await hub.send_to(cid, clientbound.LoginResponse(ok=True))
    await hub.broadcast(clientbound.LoginResponse(ok=True))

    try:
        async for raw in ws:
            data = raw if isinstance(raw, bytes) else raw.encode()
            pkt = deserialize_from_client(data)

            if isinstance(pkt, serverbound.ChatRequest):
                log.info(f"chat from {cid}: {pkt.message}")
                await hub.send_to(cid, clientbound.ChatResponse(ok=True))

            elif isinstance(pkt, serverbound.MoveRequest):
                log.info(f"move from {cid}: ({pkt.dx},{pkt.dy})")
                await hub.send_to(cid, clientbound.MoveResponse(ok=True))

            elif isinstance(pkt, serverbound.LoginRequest):
                log.info(f"login from {cid}")
                await hub.send_to(cid, clientbound.LoginResponse(ok=True))

            elif isinstance(pkt, serverbound.LogoutRequest):
                log.info(f"log out from {cid}")
                break

            elif isinstance(pkt, serverbound.RegisterRequest):
                log.info(f"register from {cid}")
                await hub.send_to(cid, clientbound.RegisterResponse(ok=True))

            else:
                log.warning(f"unhandled packet from {cid}: {pkt}")

    except Exception as exc:
        log.info(f"disconnected {cid} ({exc})")
    finally:
        _ = hub.unregister_client(cid)
        log.info(
            f"disconnected {cid} ({ws.remote_address}), total={len(hub.get_clients())}"  # pyright: ignore[reportAny]
        )


async def main() -> None:
    hub = Hub()
    async with serve(
        lambda ws: _handle_client(hub, ws),
        HOST,
        PORT,
    ):
        log.info("moonlapse server on %s:%d", HOST, PORT)
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    asyncio.run(main())
