from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, final, TypeVar, Callable, override
from abc import ABC

from demo_projects.moonlapse.shared.packets.base import Packet


class ServerboundPacketType(IntEnum):
    CHAT_REQUEST = auto()
    MOVE_REQUEST = auto()
    LOGIN_REQUEST = auto()
    LOGOUT_REQUEST = auto()
    REGISTER_REQUEST = auto()


REGISTRY: dict[int, type[ServerboundPacket]] = {}


@dataclass(frozen=True)
class ServerboundPacket(Packet, ABC):
    IS_SERVERBOUND: ClassVar[bool] = True


T = TypeVar("T", bound=ServerboundPacket)


def register() -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        REGISTRY[int(cls.TYPE)] = cls
        return cls

    return decorator


@final
@register()
@dataclass(frozen=True)
class ChatRequest(ServerboundPacket):
    TYPE = ServerboundPacketType.CHAT_REQUEST
    FORMAT_STRING = "128s"
    message: str

    @override
    def get_structure(self):
        return (self.message,)


@final
@register()
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
    key = int(packet_type)
    if key in REGISTRY:
        return REGISTRY[key]
    raise NotImplementedError(
        f"Packet type {packet_type} does not belong to serverbound registry"
    )
