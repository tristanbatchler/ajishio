from __future__ import annotations

import base64
import enum
import struct
from dataclasses import dataclass
from typing import ClassVar, Protocol, cast
from uuid import UUID


class MessageType(enum.IntEnum):
    PLAYER_POSITION = 0
    PLAYER_ID = 1
    PLAYER_X_INPUT = 2
    PLAYER_JUMP = 3
    OTHER_PLAYER_POSITION = 4
    CONNECTION_REQUEST = 5
    PLAYER_DISCONNECT = 6
    POSITION_SYNC_REQUEST = 7
    POSITION_SYNC_RESPONSE = 8


class PacketProto(Protocol):
    TAG: ClassVar[MessageType]

    def pack(self) -> str: ...

    @staticmethod
    def unpack_body(body: bytes) -> Packet | None: ...


def _encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


@dataclass(frozen=True)
class PlayerPositionPacket:
    TAG: ClassVar[MessageType] = MessageType.PLAYER_POSITION
    x: float
    y: float

    def pack(self) -> str:
        return _encode(struct.pack("!Bff", self.TAG, self.x, self.y))

    @staticmethod
    def unpack_body(body: bytes) -> PlayerPositionPacket | None:
        if len(body) != 8:
            return None
        x, y = struct.unpack("!ff", body)
        return PlayerPositionPacket(cast(float, x), cast(float, y))


@dataclass(frozen=True)
class PlayerIdPacket:
    TAG: ClassVar[MessageType] = MessageType.PLAYER_ID
    player_id: UUID

    def pack(self) -> str:
        return _encode(struct.pack("!B16s", self.TAG, self.player_id.bytes))

    @staticmethod
    def unpack_body(body: bytes) -> PlayerIdPacket | None:
        if len(body) != 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body)[0])
        return PlayerIdPacket(UUID(bytes=raw_id))


@dataclass(frozen=True)
class PlayerXInputPacket:
    TAG: ClassVar[MessageType] = MessageType.PLAYER_X_INPUT
    player_id: UUID
    x_input: int

    def pack(self) -> str:
        return _encode(struct.pack("!B16sb", self.TAG, self.player_id.bytes, self.x_input))

    @staticmethod
    def unpack_body(body: bytes) -> PlayerXInputPacket | None:
        if len(body) != 17:
            return None
        raw_id, x_input = struct.unpack("!16sb", body)
        return PlayerXInputPacket(UUID(bytes=cast(bytes, raw_id)), cast(int, x_input))


@dataclass(frozen=True)
class PlayerJumpPacket:
    TAG: ClassVar[MessageType] = MessageType.PLAYER_JUMP
    player_id: UUID

    def pack(self) -> str:
        return _encode(struct.pack("!B16s", self.TAG, self.player_id.bytes))

    @staticmethod
    def unpack_body(body: bytes) -> PlayerJumpPacket | None:
        if len(body) != 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body)[0])
        return PlayerJumpPacket(UUID(bytes=raw_id))


@dataclass(frozen=True)
class OtherPlayerPositionPacket:
    TAG: ClassVar[MessageType] = MessageType.OTHER_PLAYER_POSITION
    player_id: UUID
    x: float
    y: float

    def pack(self) -> str:
        return _encode(struct.pack("!B16sff", self.TAG, self.player_id.bytes, self.x, self.y))

    @staticmethod
    def unpack_body(body: bytes) -> OtherPlayerPositionPacket | None:
        if len(body) != 24:
            return None
        raw_id, x, y = struct.unpack("!16sff", body)
        return OtherPlayerPositionPacket(
            UUID(bytes=cast(bytes, raw_id)), cast(float, x), cast(float, y)
        )


@dataclass(frozen=True)
class ConnectionRequestPacket:
    TAG: ClassVar[MessageType] = MessageType.CONNECTION_REQUEST

    def pack(self) -> str:
        return _encode(struct.pack("!B", self.TAG))

    @staticmethod
    def unpack_body(body: bytes) -> ConnectionRequestPacket | None:
        if body:
            return None
        return ConnectionRequestPacket()


@dataclass(frozen=True)
class PlayerDisconnectPacket:
    TAG: ClassVar[MessageType] = MessageType.PLAYER_DISCONNECT
    player_id: UUID

    def pack(self) -> str:
        return _encode(struct.pack("!B16s", self.TAG, self.player_id.bytes))

    @staticmethod
    def unpack_body(body: bytes) -> PlayerDisconnectPacket | None:
        if len(body) != 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body)[0])
        return PlayerDisconnectPacket(UUID(bytes=raw_id))


@dataclass(frozen=True)
class PositionSyncRequestPacket:
    TAG: ClassVar[MessageType] = MessageType.POSITION_SYNC_REQUEST

    def pack(self) -> str:
        return _encode(struct.pack("!B", self.TAG))

    @staticmethod
    def unpack_body(body: bytes) -> PositionSyncRequestPacket | None:
        if body:
            return None
        return PositionSyncRequestPacket()


@dataclass(frozen=True)
class PositionSyncResponsePacket:
    TAG: ClassVar[MessageType] = MessageType.POSITION_SYNC_RESPONSE
    player_id: UUID
    x: float
    y: float

    def pack(self) -> str:
        return _encode(struct.pack("!B16sff", self.TAG, self.player_id.bytes, self.x, self.y))

    @staticmethod
    def unpack_body(body: bytes) -> PositionSyncResponsePacket | None:
        if len(body) != 24:
            return None
        raw_id, x, y = struct.unpack("!16sff", body)
        return PositionSyncResponsePacket(
            UUID(bytes=cast(bytes, raw_id)), cast(float, x), cast(float, y)
        )


Packet = (
    PlayerPositionPacket
    | PlayerIdPacket
    | PlayerXInputPacket
    | PlayerJumpPacket
    | OtherPlayerPositionPacket
    | ConnectionRequestPacket
    | PlayerDisconnectPacket
    | PositionSyncRequestPacket
    | PositionSyncResponsePacket
)

_REGISTRY = {
    MessageType.PLAYER_POSITION: PlayerPositionPacket,
    MessageType.PLAYER_ID: PlayerIdPacket,
    MessageType.PLAYER_X_INPUT: PlayerXInputPacket,
    MessageType.PLAYER_JUMP: PlayerJumpPacket,
    MessageType.OTHER_PLAYER_POSITION: OtherPlayerPositionPacket,
    MessageType.CONNECTION_REQUEST: ConnectionRequestPacket,
    MessageType.PLAYER_DISCONNECT: PlayerDisconnectPacket,
    MessageType.POSITION_SYNC_REQUEST: PositionSyncRequestPacket,
    MessageType.POSITION_SYNC_RESPONSE: PositionSyncResponsePacket,
}


def decode(data: bytes | str) -> Packet | None:
    try:
        raw = base64.b64decode(data)
    except Exception:
        return None

    if not raw:
        return None

    try:
        tag = MessageType(raw[0])
    except ValueError:
        return None

    cls = _REGISTRY.get(tag)
    if cls is None:
        return None

    return cls.unpack_body(raw[1:])
