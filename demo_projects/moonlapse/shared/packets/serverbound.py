from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, final, override
from abc import ABC

from demo_projects.moonlapse.shared.packets.base import Packet


class ServerboundPacketType(IntEnum):
    CHAT_REQUEST = auto()
    MOVE_REQUEST = auto()
    LOGIN_REQUEST = auto()
    LOGOUT_REQUEST = auto()
    REGISTER_REQUEST = auto()


@dataclass(frozen=True)
class ServerboundPacket(Packet, ABC):
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


@final
@dataclass(frozen=True)
class MoveRequest(ServerboundPacket):
    TYPE = ServerboundPacketType.MOVE_REQUEST
    FORMAT_STRING = "bb"
    dx: int
    dy: int

    @override
    def get_structure(self):
        return (self.dx, self.dy)


def get_packet_class(packet_type: ServerboundPacketType) -> type[ServerboundPacket]:
    match packet_type:
        case ServerboundPacketType.CHAT_REQUEST:
            return ChatRequest
        case ServerboundPacketType.MOVE_REQUEST:
            return MoveRequest
        case _:
            raise NotImplementedError(
                f"Packet type {packet_type} does not belong to serverbound registry"
            )
