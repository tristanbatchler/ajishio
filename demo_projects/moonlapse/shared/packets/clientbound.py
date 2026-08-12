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
    CLIENT_DISCONNECTED = auto()
    MOTD = auto()
    ANNOUNCEMENT = auto()
    PLAYER_CHAT = auto()


REGISTRY: dict[ClientboundPacketType, type[ClientboundPacket]] = {}


@dataclass(frozen=True)
class ClientboundPacket(Packet, ABC):
    IS_SERVERBOUND: ClassVar[bool] = False


T = TypeVar("T", bound=ClientboundPacket)


def register(packet_type: ClientboundPacketType) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        cls.TYPE = packet_type
        REGISTRY[cls.TYPE] = cls
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
@register(ClientboundPacketType.CHAT_RESPONSE)
@dataclass(frozen=True)
class ChatResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.MOVE_RESPONSE)
@dataclass(frozen=True)
class MoveResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.LOGIN_RESPONSE)
@dataclass(frozen=True)
class LoginResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.LOGOUT_RESPONSE)
@dataclass(frozen=True)
class LogoutResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.REGISTER_RESPONSE)
@dataclass(frozen=True)
class RegisterResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.CLIENT_ID)
@dataclass(frozen=True)
class ClientId(ClientboundPacket):
    FORMAT_STRING = "I"
    id: int

    @override
    def get_structure(self):
        return (self.id,)


@final
@register(ClientboundPacketType.PLAYER_INFO)
@dataclass(frozen=True)
class PlayerInfo(ClientboundPacket):
    FORMAT_STRING = "128sii"
    name: str
    x_pos: int
    y_pos: int

    @override
    def get_structure(self):
        return (self.name, self.x_pos, self.y_pos)


@final
@register(ClientboundPacketType.CLIENT_DISCONNECTED)
@dataclass(frozen=True)
class ClientDisconnected(ClientboundPacket):
    FORMAT_STRING = "I128s"
    client_id: int
    reason: str | None = None

    @override
    def get_structure(self):
        return (self.client_id, self.reason or "N/A")


@final
@register(ClientboundPacketType.MOTD)
@dataclass(frozen=True)
class Motd(ClientboundPacket):
    FORMAT_STRING = "512s"
    motd: str

    @override
    def get_structure(self):
        return (self.motd,)


@final
@register(ClientboundPacketType.ANNOUNCEMENT)
@dataclass(frozen=True)
class Announcement(ClientboundPacket):
    FORMAT_STRING = "512s"
    message: str

    @override
    def get_structure(self):
        return (self.message,)


@final
@register(ClientboundPacketType.PLAYER_CHAT)
@dataclass(frozen=True)
class PlayerChat(ClientboundPacket):
    FORMAT_STRING = "I256s"
    from_client_id: int
    message: str

    @override
    def get_structure(self):
        return (self.from_client_id, self.message)
