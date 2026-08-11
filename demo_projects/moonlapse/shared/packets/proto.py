from __future__ import annotations
from collections.abc import Iterable
import struct

from typing import ClassVar, Protocol, runtime_checkable


def _clean_structure(structure: Iterable[object]) -> Iterable[object]:
    for obj in structure:
        if isinstance(obj, str):
            yield obj.encode()
        else:
            yield obj


@runtime_checkable
class PacketProto(Protocol):
    TYPE: ClassVar[int]
    IS_SERVERBOUND: ClassVar[bool]
    FORMAT_STRING: ClassVar[str]

    def get_structure(self) -> tuple[object, ...]: ...

    @classmethod
    def from_bytes(cls, data: bytes) -> PacketProto:
        fmt = cls.FORMAT_STRING
        structure = _clean_structure(struct.unpack(fmt, data))
        return cls(*structure)

    def serialize(self) -> bytes:
        ptype = self.TYPE
        header_bytes = struct.pack(">H", ptype)
        structure = _clean_structure(self.get_structure())
        payload_bytes = struct.pack(self.FORMAT_STRING, *structure)
        return header_bytes + payload_bytes
