from __future__ import annotations
from collections.abc import Iterable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import struct

from typing import ClassVar, Self, cast


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


@dataclass
class _Bounds:
    signed_lower: int
    signed_upper: int
    unsigned_lower: int
    unsigned_upper: int


def _ctype_bounds(n_bytes: int) -> _Bounds:
    bits = n_bytes * 8

    unsigned_upper = cast(int, 2**bits - 1)
    signed_upper = cast(int, 2 ** (bits - 1) - 1)

    unsigned_lower = 0
    signed_lower = -signed_upper - 1

    return _Bounds(signed_lower, signed_upper, unsigned_lower, unsigned_upper)


_char_bounds = _ctype_bounds(1)
_short_bounds = _ctype_bounds(2)
_long_bounds = _ctype_bounds(4)
_long_long_bounds = _ctype_bounds(8)


class Packet(ABC):
    # TYPE is injected by @register, so set a default pyright is happy with here
    TYPE: ClassVar[int] = cast(int, cast(object, None))

    @abstractmethod
    def get_structure(self) -> tuple[object, ...]: ...

    def get_fmt_string(self) -> str:
        fmt_str = ""
        for p in self.get_structure():
            match p:
                case str():
                    fmt_str += f"{len(p)}s"
                case int():
                    if p < _long_bounds.signed_lower:
                        fmt_str += "q"  # long long
                    elif p < _short_bounds.signed_lower:
                        fmt_str += "l"  # long
                    elif p < _char_bounds.signed_lower:
                        fmt_str += "h"  # short
                    elif p < 0:
                        fmt_str += "b"  # char
                    elif p <= _char_bounds.unsigned_upper:
                        fmt_str += "B"  # unsigned char
                    elif p <= _short_bounds.unsigned_upper:
                        fmt_str += "H"  # unsigned short
                    elif p <= _long_bounds.unsigned_upper:
                        fmt_str += "L"  # unsigned long
                    else:
                        fmt_str += "Q"  # unsigned long long
                case bool():
                    fmt_str += "?"
                case float():
                    fmt_str += "d"  # double
                case _:
                    raise NotImplementedError(
                        f"Can't pack struct member {p} because we don't support a format string for its packing"
                    )
        return fmt_str

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        header, payload = data.split(b"|", 1)
        fmt_str = header.decode()
        structure = _decode_structure(struct.unpack(fmt_str, payload))
        return cls(*structure)

    def to_bytes(self) -> bytes:
        fmt_str = self.get_fmt_string()
        header_bytes = struct.pack(
            f"!{len(fmt_str)}s",
            fmt_str.encode(),  # The first part is payload-unpacking instructions
        )
        structure = _encode_structure(self.get_structure())
        payload_bytes = struct.pack(
            fmt_str,
            *structure,  # The second part is the actual data
        )
        return header_bytes + b"|" + payload_bytes

    def serialize(self) -> bytes:
        fmt_str = self.get_fmt_string()
        header_bytes = struct.pack(
            f"!H{len(fmt_str)}s",
            self.TYPE,
            fmt_str.encode(),  # The first part a fixed 2 bytes containing the packet type enum, followed by payload-unpacking instructions
        )
        structure = _encode_structure(self.get_structure())
        payload_bytes = struct.pack(
            fmt_str,
            *structure,  # The second part is the actual data
        )
        return header_bytes + b"|" + payload_bytes
