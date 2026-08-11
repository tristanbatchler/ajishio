from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, override, final
from abc import ABC

from demo_projects.moonlapse.shared.packets.base import Packet


class ClientboundPacketType(IntEnum):
    CHAT_RESPONSE = auto()
    MOVE_RESPONSE = auto()
    LOGIN_RESPONSE = auto()
    LOGOUT_RESPONSE = auto()
    REGISTER_RESPONSE = auto()


@dataclass(frozen=True)
class ClientboundPacket(Packet, ABC):
    IS_SERVERBOUND: ClassVar[bool] = False


@dataclass(frozen=True)
class ClientboundResponsePacket(ClientboundPacket, ABC):
    FORMAT_STRING: ClassVar[str] = "?128s"

    ok: bool
    err: str | None = None

    @override
    def get_structure(self):
        return (self.ok, self.err or "")


@final
@dataclass(frozen=True)
class ChatResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.CHAT_RESPONSE


@final
@dataclass(frozen=True)
class MoveResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.MOVE_RESPONSE


def get_packet_class(packet_type: ClientboundPacketType) -> type[ClientboundPacket]:
    match packet_type:
        case ClientboundPacketType.CHAT_RESPONSE:
            return ChatResponse
        case ClientboundPacketType.MOVE_RESPONSE:
            return MoveResponse
        case _:
            raise NotImplementedError(
                f"Packet type {packet_type} does not belong to clientbound registry"
            )
