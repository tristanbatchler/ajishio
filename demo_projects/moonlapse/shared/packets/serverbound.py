from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, final, override, Protocol

from demo_projects.moonlapse.shared.packets.proto import PacketProto


class ServerboundPacketType(IntEnum):
    CHAT_REQUEST = auto()
    MOVE_REQUEST = auto()
    LOGIN_REQUEST = auto()
    LOGOUT_REQUEST = auto()
    REGISTER_REQUEST = auto()


@dataclass(frozen=True)
class ServerboundPacket(PacketProto, Protocol):
    IS_SERVERBOUND: ClassVar[bool] = True


@final
@dataclass(frozen=True)
class ChatRequest(ServerboundPacket):
    TYPE = ServerboundPacketType.CHAT_REQUEST
    FORMAT_STRING = "128s"
    message: str

    @override
    def get_structure(self):
        return (self.message,)


REGISTRY: dict[int, type[PacketProto]] = {
    ServerboundPacketType.CHAT_REQUEST: ChatRequest,
}
