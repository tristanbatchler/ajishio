from __future__ import annotations

import logging
from demo_projects.moonlapse.shared.packets import clientbound
from demo_projects.moonlapse.server.client import Client

log = logging.getLogger("moonlapse.connection")


class Hub:
    def __init__(self) -> None:
        self._next_id: int = 1
        self._clients: dict[int, Client] = {}

    @property
    def next_id(self) -> int:
        cid = self._next_id
        self._next_id += 1
        return cid

    def register_client(self, client: Client) -> None:
        self._clients[client.id] = client

    def unregister_client(self, client_id: int) -> Client | None:
        return self._clients.pop(client_id, None)

    def get_clients(self) -> list[Client]:
        return list(self._clients.values())

    async def send_to(
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
        except_for: int | None = None,
    ) -> None:
        for cid, client in self._clients.items():
            if cid == except_for:
                continue
            try:
                await client.ws.send(packet.serialize())
            except Exception as exc:
                log.warning(f"broadcast failed to {cid}: {exc}")
