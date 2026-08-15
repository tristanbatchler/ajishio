from __future__ import annotations

import asyncio
from websockets.asyncio.server import ServerConnection
from demo_projects.moonlapse.server.state import State
from demo_projects.moonlapse.shared.packets.serverbound import ServerboundPacket
from dataclasses import dataclass, field


@dataclass
class Client:
    """Connection-specific properties for a client connected to the hub."""

    id: int
    ws: ServerConnection
    state: State | None = None
    input_packet_queue: asyncio.Queue[ServerboundPacket] = field(
        default_factory=asyncio.Queue
    )

    @property
    def ip_address(self) -> str:
        return self.ws.remote_address[0]  # pyright: ignore[reportAny]
