from __future__ import annotations
import struct

from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class PacketProto(Protocol):
    TYPE: ClassVar[int]
    IS_SERVERBOUND: ClassVar[bool]

    @staticmethod
    def get_fmt() -> str: ...
    def get_structure(self) -> tuple[object, ...]: ...

    @classmethod
    def from_bytes(cls, data: bytes) -> PacketProto:
        fmt = cls.get_fmt()
        unpacked = struct.unpack(fmt, data)
        return cls(*unpacked)

    def serialize(self) -> bytes:
        ptype = self.TYPE
        fmt = self.get_fmt()
        structure = self.get_structure()
        header_bytes = struct.pack(">H", ptype)
        payload_bytes = struct.pack(fmt, *structure)
        return header_bytes + payload_bytes
