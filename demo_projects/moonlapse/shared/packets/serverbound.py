from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar
import struct

from demo_projects.moonlapse.shared.packets.proto import PacketProto


class ServerboundPacketType(IntEnum):
    CHAT_REQUEST = auto()
    MOVE_REQUEST = auto()
    LOGIN_REQUEST = auto()
    LOGOUT_REQUEST = auto()
    REGISTER_REQUEST = auto()


@dataclass(frozen=True)
class ChatRequest:
    IS_SERVERBOUND: ClassVar[bool] = True
    TYPE: ClassVar[ServerboundPacketType] = ServerboundPacketType.CHAT_REQUEST

    message: str

    def get_type(self) -> int:
        return int(self.TYPE)

    def get_fmt(self) -> str:
        return ">127s"

    def get_structure(self) -> tuple[object, ...]:
        return (self.message.encode(),)

    @classmethod
    def from_bytes(cls, data: bytes) -> ChatRequest:
        unpacked: tuple[bytes, ...] = struct.unpack(">127s", data)
        raw: bytes = unpacked[0]
        msg = raw.rstrip(b"\x00").decode("utf-8")
        return cls(message=msg)


REGISTRY: dict[int, type[PacketProto]] = {
    int(ServerboundPacketType.CHAT_REQUEST): ChatRequest,
}
