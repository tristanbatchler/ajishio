import asyncio
from websockets.asyncio.server import ServerConnection
from demo_projects.moonlapse.server.state import State
from demo_projects.moonlapse.shared.packets.serverbound import ServerboundPacket
from dataclasses import dataclass, field


@dataclass
class Client:
    id: int
    ws: ServerConnection
    state: State | None = None
    input_packet_queue: asyncio.Queue[ServerboundPacket] = field(
        default_factory=asyncio.Queue
    )
