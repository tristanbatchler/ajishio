from __future__ import annotations
from collections.abc import Iterable
from abc import ABC, abstractmethod
import struct

from typing import ClassVar, Self


def _encode_structure(structure: Iterable[object]) -> Iterable[object]:
    for obj in structure:
        if isinstance(obj, str):
            yield obj.encode()
        else:
            yield obj


def _decode_structure(structure: Iterable[object]) -> Iterable[object]:
    for obj in structure:
        if isinstance(obj, bytes):
            yield obj.rstrip(b"\x00").decode()
        else:
            yield obj


class Packet(ABC):
    TYPE: ClassVar[int]
    IS_SERVERBOUND: ClassVar[bool]
    FORMAT_STRING: ClassVar[str]

    @abstractmethod
    def get_structure(self) -> tuple[object, ...]: ...

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        fmt = cls.FORMAT_STRING
        structure = _decode_structure(struct.unpack(fmt, data))
        return cls(*structure)

    def serialize(self) -> bytes:
        ptype = self.TYPE
        header_bytes = struct.pack(">H", ptype)
        structure = _encode_structure(self.get_structure())
        payload_bytes = struct.pack(self.FORMAT_STRING, *structure)
        return header_bytes + payload_bytes
