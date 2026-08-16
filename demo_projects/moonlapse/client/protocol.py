from __future__ import annotations

import ajishio as aj
from typing import ClassVar, Protocol
from abc import ABC, abstractmethod
import demo_projects.moonlapse.shared.packets.clientbound as clientbound


class ManagerLike(Protocol):
    client: aj.GameNetClient

    def set_client_id(self, id: int) -> None: ...
    def get_client_id(self) -> int | None: ...


class State(aj.IGameObject, ABC):
    NAME: ClassVar[str]

    @abstractmethod
    def on_enter(self) -> None: ...

    @abstractmethod
    def on_exit(self) -> None: ...

    @abstractmethod
    def handle_packet(self, p: clientbound.ClientboundPacket) -> State | None: ...
