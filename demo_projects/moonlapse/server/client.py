from websockets.asyncio.server import ServerConnection
from demo_projects.moonlapse.server.state import State
from dataclasses import dataclass


@dataclass
class Client:
    id: int
    ws: ServerConnection
    state: State | None = None
