from __future__ import annotations

import ajishio as aj
from typing import ClassVar, Protocol
from abc import ABC, abstractmethod
from demo_projects.moonlapse.shared.packets.clientbound import ClientboundPacket
from demo_projects.moonlapse.shared.packets.serverbound import ServerboundPacket


class ManagerLike(Protocol):
    def set_client_id(self, id: int) -> None: ...
    def get_client_id(self) -> int | None: ...
    def send(self, p: ServerboundPacket) -> None: ...


class State(aj.IGameObject, ABC):
    NAME: ClassVar[str]

    @abstractmethod
    def on_enter(self) -> None: ...

    @abstractmethod
    def on_exit(self) -> None: ...

    @abstractmethod
    def handle_packet(self, p: ClientboundPacket) -> State | None: ...
