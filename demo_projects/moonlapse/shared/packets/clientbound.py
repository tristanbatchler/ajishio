from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import ClassVar, final
import struct

from demo_projects.moonlapse.shared.packets.proto import PacketProto

_CLIENTBOUND_OFFSET: int = 1000


def offset_type(raw_type: int) -> int:
    return raw_type + _CLIENTBOUND_OFFSET


class ClientboundPacketType(IntEnum):
    CHAT_RESPONSE = auto()
    MOVE_RESPONSE = auto()
    LOGIN_RESPONSE = auto()
    LOGOUT_RESPONSE = auto()
    REGISTER_RESPONSE = auto()


@final
@dataclass(frozen=True)
class ChatResponse:
    IS_SERVERBOUND: ClassVar[bool] = False
    TYPE: ClassVar[ClientboundPacketType] = ClientboundPacketType.CHAT_RESPONSE

    ok: bool
    err: str | None

    def get_type(self) -> int:
        return offset_type(int(self.TYPE))

    def get_fmt(self) -> str:
        return ">B128s"

    def get_structure(self) -> tuple[object, ...]:
        return (self.ok, self.err.encode() if self.err else b"\x00" * 128)

    @classmethod
    def from_bytes(cls, data: bytes) -> ChatResponse:
        unpacked: tuple[bool, bytes] = struct.unpack(">B128s", data)
        ok: bool = unpacked[0]
        err_bytes: bytes = unpacked[1]
        err_str = err_bytes.decode("utf-8").rstrip("\x00") or None
        return cls(ok=bool(ok), err=err_str)


REGISTRY: dict[int, type[PacketProto]] = {
    offset_type(int(ClientboundPacketType.CHAT_RESPONSE)): ChatResponse,
}
