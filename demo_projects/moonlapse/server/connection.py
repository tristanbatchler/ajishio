from __future__ import annotations

import logging
from collections.abc import Set

import aiosqlite
from websockets.asyncio.server import ServerConnection
from demo_projects.moonlapse.shared.packets import clientbound, deserialize_from_client
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.states import ConnectedState

log = logging.getLogger("moonlapse.connection")


class Hub:
    def __init__(self, db_conn: aiosqlite.Connection) -> None:
        self._next_id: int = 1
        self._clients: dict[int, Client] = {}
        self.db_conn: aiosqlite.Connection = db_conn

    @property
    def next_id(self) -> int:
        cid = self._next_id
        self._next_id += 1
        return cid

    def unregister_client(self, client_id: int) -> Client | None:
        return self._clients.pop(client_id, None)

    def get_clients(self) -> list[Client]:
        return list(self._clients.values())

    async def register_client(self, ws: ServerConnection) -> None:
        cid = self.next_id
        client = Client(cid, ws)
        client.state = ConnectedState(client, self)
        self._clients[cid] = client

        try:
            await client.state.on_enter()

            async for raw in client.ws:
                data = raw if isinstance(raw, bytes) else raw.encode()
                packet = deserialize_from_client(data)

                new_state = await client.state.handle_packet(packet)

                if new_state is not None:
                    await client.state.on_exit()
                    client.state = new_state
                    await client.state.on_enter()

        except Exception as exc:
            log.info("client %d disconnected: %s", cid, exc)

        finally:
            _ = self.unregister_client(cid)
            await self.broadcast(
                clientbound.Announcement(f"Player {cid} left the game.")
            )
            log.info(
                "disconnected %d (%s), total=%d",
                cid,
                client.ws.remote_address,  # pyright: ignore[reportAny]
                len(self.get_clients()),
            )

    async def send_client_ws(
        self, client_id: int, packet: clientbound.ClientboundPacket
    ) -> None:
        session = self._clients.get(client_id)
        if session is not None:
            try:
                await session.ws.send(packet.serialize())
            except Exception as exc:
                log.warning(f"send_to {client_id} failed: {exc}")

    async def broadcast(
        self,
        packet: clientbound.ClientboundPacket,
        only_to: Set[int] | None = None,
        except_for: Set[int] | None = None,
    ) -> None:
        if only_to is None:
            only_to = self._clients.keys()
        if except_for is None:
            except_for = set()
        recipients = only_to - except_for
        for cid in recipients:
            client = self._clients[cid]
            try:
                await client.ws.send(packet.serialize())
            except Exception as exc:
                log.warning(f"broadcast failed to {cid}: {exc}")

    async def close(self) -> None:
        await self.db_conn.close()
