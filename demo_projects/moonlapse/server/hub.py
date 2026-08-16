from typing import Protocol
from collections.abc import Set

import aiosqlite
from websockets.asyncio.server import ServerConnection
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.shared.packets.clientbound import ClientboundPacket


class HubLike(Protocol):
    db_conn: aiosqlite.Connection

    @property
    def next_entity_id(self) -> int: ...

    async def register_client(self, ws: ServerConnection) -> None: ...
    def unregister_client(self, client_id: int) -> Client | None: ...
    def get_clients(self) -> list[Client]: ...
    async def send_client_ws(
        self, client_id: int, packet: ClientboundPacket
    ) -> None: ...
    async def broadcast(
        self,
        packet: ClientboundPacket,
        only_to: Set[int] | None = None,
        except_for: Set[int] | None = None,
    ) -> None: ...
