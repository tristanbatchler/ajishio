from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, override, Protocol, final

from demo_projects.moonlapse.shared.packets.proto import PacketProto


class ClientboundPacketType(IntEnum):
    CHAT_RESPONSE = 1000  # offset to avoid collision with serverbound registry
    MOVE_RESPONSE = auto()
    LOGIN_RESPONSE = auto()
    LOGOUT_RESPONSE = auto()
    REGISTER_RESPONSE = auto()


@dataclass(frozen=True)
class ClientboundPacket(PacketProto, Protocol):
    IS_SERVERBOUND: ClassVar[bool] = False


@final
@dataclass(frozen=True)
class ChatResponse(ClientboundPacket):
    TYPE = ClientboundPacketType.CHAT_RESPONSE
    ok: bool
    err: str | None

    @override
    @staticmethod
    def get_fmt() -> str:
        return ">B128s"

    @override
    def get_structure(self) -> tuple[object, ...]:
        return (self.ok, self.err.encode() if self.err else b"\x00" * 128)


REGISTRY: dict[int, type[PacketProto]] = {
    ClientboundPacketType.CHAT_RESPONSE: ChatResponse,
}
