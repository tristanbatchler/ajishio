from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, override, final, TypeVar, Callable
from abc import ABC

from demo_projects.moonlapse.shared.packets.base import Packet


class ClientboundPacketType(IntEnum):
    CHAT_RESPONSE = auto()
    MOVE_RESPONSE = auto()
    LOGIN_RESPONSE = auto()
    LOGOUT_RESPONSE = auto()
    REGISTER_RESPONSE = auto()
    CLIENT_ID = auto()
    PLAYER_INFO = auto()


REGISTRY: dict[int, type[ClientboundPacket]] = {}


@dataclass(frozen=True)
class ClientboundPacket(Packet, ABC):
    IS_SERVERBOUND: ClassVar[bool] = False


T = TypeVar("T", bound=ClientboundPacket)


def register() -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        REGISTRY[int(cls.TYPE)] = cls
        return cls

    return decorator


@dataclass(frozen=True)
class ClientboundResponsePacket(ClientboundPacket, ABC):
    FORMAT_STRING: ClassVar[str] = "?128s"

    ok: bool
    err: str | None = None

    @override
    def get_structure(self):
        return (self.ok, self.err or "")


@final
@register()
@dataclass(frozen=True)
class ChatResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.CHAT_RESPONSE


@final
@register()
@dataclass(frozen=True)
class MoveResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.MOVE_RESPONSE


@final
@register()
@dataclass(frozen=True)
class LoginResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.LOGIN_RESPONSE


@final
@register()
@dataclass(frozen=True)
class LogoutResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.LOGOUT_RESPONSE


@final
@register()
@dataclass(frozen=True)
class RegisterResponse(ClientboundResponsePacket):
    TYPE = ClientboundPacketType.REGISTER_RESPONSE


@final
@register()
@dataclass(frozen=True)
class ClientId(ClientboundPacket):
    TYPE = ClientboundPacketType.CLIENT_ID
    FORMAT_STRING = "I"
    id: int

    @override
    def get_structure(self):
        return (self.id,)


@final
@register()
@dataclass(frozen=True)
class PlayerInfo(ClientboundPacket):
    TYPE = ClientboundPacketType.PLAYER_INFO
    FORMAT_STRING = "128sii"
    name: str
    x_pos: int
    y_pos: int

    @override
    def get_structure(self):
        return (self.name, self.x_pos, self.y_pos)


def get_packet_class(packet_type: ClientboundPacketType) -> type[ClientboundPacket]:
    key = int(packet_type)
    if key in REGISTRY:
        return REGISTRY[key]
    raise NotImplementedError(f"Packet type {packet_type} does not belong to clientbound registry")
