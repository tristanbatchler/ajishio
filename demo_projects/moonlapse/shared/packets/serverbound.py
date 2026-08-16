from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import final, TypeVar, Callable, override
from abc import ABC

from demo_projects.moonlapse.shared.packets.base import Packet


class ServerboundPacketType(IntEnum):
    CHAT_REQUEST = auto()
    MOVE_REQUEST = auto()
    LOGIN_REQUEST = auto()
    LOGOUT_REQUEST = auto()
    REGISTER_REQUEST = auto()
    ENTITY_MOVE_REQUEST = auto()


REGISTRY: dict[ServerboundPacketType, type[ServerboundPacket]] = {}


@dataclass(frozen=True)
class ServerboundPacket(Packet, ABC): ...


T = TypeVar("T", bound=ServerboundPacket)


def register(packet_type: ServerboundPacketType) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        cls.TYPE = packet_type
        REGISTRY[cls.TYPE] = cls
        return cls

    return decorator


@final
@register(ServerboundPacketType.CHAT_REQUEST)
@dataclass(frozen=True)
class ChatRequest(ServerboundPacket):
    FORMAT_STRING = "256s"
    message: str

    @override
    def get_structure(self):
        return (self.message,)


@final
@register(ServerboundPacketType.MOVE_REQUEST)
@dataclass(frozen=True)
class MoveRequest(ServerboundPacket):
    FORMAT_STRING = "bb"
    dx: int
    dy: int

    @override
    def get_structure(self):
        return (self.dx, self.dy)


@final
@register(ServerboundPacketType.LOGIN_REQUEST)
@dataclass(frozen=True)
class LoginRequest(ServerboundPacket):
    FORMAT_STRING = "128s128s"
    username: str
    password: str

    @override
    def get_structure(self):
        return (self.username, self.password)


@final
@register(ServerboundPacketType.LOGOUT_REQUEST)
@dataclass(frozen=True)
class LogoutRequest(ServerboundPacket):
    FORMAT_STRING = ""

    @override
    def get_structure(self):
        return ()


@final
@register(ServerboundPacketType.REGISTER_REQUEST)
@dataclass(frozen=True)
class RegisterRequest(ServerboundPacket):
    FORMAT_STRING = "128s128s"
    username: str
    password: str

    @override
    def get_structure(self):
        return (self.username, self.password)


@final
@register(ServerboundPacketType.ENTITY_MOVE_REQUEST)
@dataclass(frozen=True)
class EntityMoveRequest(ServerboundPacket):
    FORMAT_STRING = "Ibb"
    entity_id: int
    dx: int
    dy: int

    @override
    def get_structure(self):
        return (self.entity_id, self.dx, self.dy)
