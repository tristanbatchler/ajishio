from typing import Protocol, ClassVar
from demo_projects.moonlapse.shared.packets.serverbound import ServerboundPacket


class State(Protocol):
    NAME: ClassVar[str]

    async def on_enter(self) -> None: ...
    async def on_exit(self) -> None: ...
    async def handle_packet(self, p: ServerboundPacket) -> State | None: ...
