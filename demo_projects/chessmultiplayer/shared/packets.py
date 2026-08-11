"""Binary packet protocol for the chess multiplayer demo.

Wire format
-----------
Every packet is a single WebSocket frame containing a **base64-encoded**
binary blob.  The underlying binary layout is:

    [1 byte type tag] [N bytes body]
"""

from __future__ import annotations

import base64
from enum import IntEnum, auto
import struct
from dataclasses import dataclass
from typing import ClassVar, Protocol, cast
from uuid import UUID
from demo_projects.chessmultiplayer.shared.chess import Role


class PacketProto(Protocol):
    """Structural interface every concrete packet must satisfy."""

    TAG: ClassVar[PacketType]

    def encode(self) -> str: ...

    @staticmethod
    def unpack_body(body: bytes) -> PacketProto | None: ...


class PacketType(IntEnum):
    """Single-byte discriminator written at the start of every packet."""

    ASSIGN_ID = auto()
    BOARD_STATE = auto()
    MOVE_REQUEST = auto()
    MOVE_RESULT = auto()
    GAME_START = auto()
    CLIENT_CONNECTED = auto()
    CLIENT_DISCONNECTED = auto()
    CHAT = auto()
    LOBBY_UPDATE = auto()
    GAME_OVER = auto()
    JOIN = auto()


class LobbyStatus(IntEnum):
    WAITING = auto()
    MATCH_FOUND = auto()
    GAME_FULL = auto()
    OPPONENT_LEFT = auto()
    CONNECTING = auto()
    PLAYING = auto()
    REJOINING = auto()
    GAME_OVER = auto()


@dataclass(frozen=True)
class Join:
    """Client → server. Request a new lobby slot."""

    TAG: ClassVar[PacketType] = PacketType.JOIN

    def encode(self) -> str:
        return base64.b64encode(struct.pack("!B", PacketType.JOIN.value)).decode()

    @staticmethod
    def unpack_body(body: bytes) -> Join | None:
        if len(body) != 0:
            return None
        return Join()


@dataclass(frozen=True)
class GameOver:
    """Announces game end."""

    TAG: ClassVar[PacketType] = PacketType.GAME_OVER
    winner: Role
    reason: str

    def encode(self) -> str:
        raw = struct.pack("!B", PacketType.GAME_OVER.value)
        raw += struct.pack("!B", self.winner.value)
        text = self.reason.encode("utf-8")
        raw += struct.pack("!B", len(text)) + text
        return base64.b64encode(raw).decode()

    @staticmethod
    def unpack_body(body: bytes) -> GameOver | None:
        if len(body) < 2:
            return None
        (winner_raw,) = cast(tuple[int], struct.unpack("!B", body[:1]))
        (text_len,) = cast(tuple[int], struct.unpack("!B", body[1:2]))
        if len(body) < 2 + text_len:
            return None
        text = body[2 : 2 + text_len].decode("utf-8")
        return GameOver(winner=Role(winner_raw), reason=text)


@dataclass(frozen=True)
class AssignId:
    TAG: ClassVar[PacketType] = PacketType.ASSIGN_ID
    sender_id: UUID

    def encode(self) -> str:
        return base64.b64encode(struct.pack("!B", self.TAG.value) + self.sender_id.bytes).decode()

    @staticmethod
    def unpack_body(body: bytes) -> AssignId | None:
        if len(body) != 16:
            return None
        return AssignId(sender_id=UUID(bytes=body))


@dataclass(frozen=True)
class GameStart:
    """Signals that the game is ready.

    Fixed body: white_id (16 bytes) + black_id (16 bytes).
    Zeroed UUID (0000-0000-0000-0000-0000) means "no black yet".
    """

    _UUID_LEN: ClassVar[int] = 16
    _ZERO_UUID: ClassVar[bytes] = b"\x00" * _UUID_LEN

    TAG: ClassVar[PacketType] = PacketType.GAME_START
    white_id: UUID
    black_id: UUID | None = None

    def encode(self) -> str:
        raw = struct.pack("!B", self.TAG.value)
        raw += self.white_id.bytes
        raw += self.black_id.bytes if self.black_id is not None else self._ZERO_UUID
        return base64.b64encode(raw).decode()

    @staticmethod
    def unpack_body(body: bytes) -> GameStart | None:
        UUID_LEN = GameStart._UUID_LEN
        if len(body) != UUID_LEN * 2:
            return None
        white = UUID(bytes=body[:UUID_LEN])
        black_raw = body[UUID_LEN : UUID_LEN * 2]
        black_id: UUID | None = None if black_raw == GameStart._ZERO_UUID else UUID(bytes=black_raw)
        return GameStart(white_id=white, black_id=black_id)


@dataclass(frozen=True)
class BoardStateWire:
    """Full board — 64 raw bytes + 1 byte next_turn."""

    TAG: ClassVar[PacketType] = PacketType.BOARD_STATE
    grid: bytes
    next_turn: Role

    def encode(self) -> str:
        return base64.b64encode(
            struct.pack("!B", PacketType.BOARD_STATE.value)
            + self.grid
            + struct.pack("!B", self.next_turn.value)
        ).decode()

    @staticmethod
    def unpack_body(body: bytes) -> BoardStateWire | None:
        if len(body) < 65:
            return None
        grid = body[:64]
        next_turn = body[64]
        return BoardStateWire(grid=grid, next_turn=Role(next_turn))


@dataclass(frozen=True)
class MoveRequest:
    """Client → server.

    Body: ``!BBB BB`` (from_col, from_row, to_col, to_row).
    The server infers sender_id from the connection.
    """

    TAG: ClassVar[PacketType] = PacketType.MOVE_REQUEST
    from_col: int
    from_row: int
    to_col: int
    to_row: int

    def encode(self) -> str:
        return base64.b64encode(
            struct.pack("!B", PacketType.MOVE_REQUEST.value)
            + struct.pack("!BBBB", self.from_col, self.from_row, self.to_col, self.to_row)
        ).decode()

    @staticmethod
    def unpack_body(body: bytes) -> MoveRequest | None:
        if len(body) != 4:
            return None
        fc, fr, tc, tr = cast(tuple[int, int, int, int], struct.unpack("!BBBB", body))
        return MoveRequest(from_col=fc, from_row=fr, to_col=tc, to_row=tr)


@dataclass(frozen=True)
class MoveResult:
    """Server → client.  Acknowledge or reject.

    Body: ``!BB`` (success=0 or fail=1, err_len) ``err``
    """

    TAG: ClassVar[PacketType] = PacketType.MOVE_RESULT
    success: bool
    error: str = ""

    def encode(self) -> str:
        err = self.error.encode()
        raw = struct.pack("!B", PacketType.MOVE_RESULT.value)
        raw += struct.pack("!BB", 0 if self.success else 1, len(err))
        raw += err
        return base64.b64encode(raw).decode()

    @staticmethod
    def unpack_body(body: bytes) -> MoveResult | None:
        if len(body) < 2:
            return None
        (is_fail, err_len) = cast(tuple[int, int], struct.unpack("!BB", body[:2]))
        if len(body) < 2 + err_len:
            return None
        err = body[2 : 2 + err_len].decode("utf-8") if err_len else ""
        return MoveResult(success=not bool(is_fail), error=err)


@dataclass(frozen=True)
class LobbyUpdate:
    """Server → client.  Lobby state changes."""

    TAG: ClassVar[PacketType] = PacketType.LOBBY_UPDATE
    status: LobbyStatus
    white_id: UUID | None = None
    black_id: UUID | None = None

    def encode(self) -> str:
        tag_byte = struct.pack("!B", PacketType.LOBBY_UPDATE.value)
        status_str = self.status.name.lower()
        status_bytes = status_str.encode()
        if self.white_id and self.black_id:
            return base64.b64encode(
                tag_byte
                + struct.pack("!B", len(status_bytes))
                + status_bytes
                + self.white_id.bytes
                + self.black_id.bytes
            ).decode()
        if self.white_id:
            return base64.b64encode(
                tag_byte + struct.pack("!B", len(status_bytes)) + status_bytes + self.white_id.bytes
            ).decode()
        return base64.b64encode(
            tag_byte + struct.pack("!B", len(status_bytes)) + status_bytes
        ).decode()

    @staticmethod
    def unpack_body(body: bytes) -> LobbyUpdate | None:
        if len(body) < 2:
            return None
        (status_len,) = cast(tuple[int], struct.unpack("!B", body[:1]))
        status_name = body[1 : 1 + status_len].decode("utf-8")
        try:
            status = LobbyStatus[status_name.upper()]
        except KeyError:
            return None
        remaining = body[1 + status_len :]
        if len(remaining) >= 32:
            return LobbyUpdate(
                status=status,
                white_id=UUID(bytes=remaining[:16]),
                black_id=UUID(bytes=remaining[16:32]),
            )
        if len(remaining) >= 16:
            return LobbyUpdate(status=status, white_id=UUID(bytes=remaining[:16]))
        return LobbyUpdate(status=status)


@dataclass(frozen=True)
class ClientConnected:
    TAG: ClassVar[PacketType] = PacketType.CLIENT_CONNECTED
    client_id: UUID

    def encode(self) -> str:
        return base64.b64encode(struct.pack("!B", self.TAG.value) + self.client_id.bytes).decode()

    @staticmethod
    def unpack_body(body: bytes) -> ClientConnected | None:
        if len(body) != 16:
            return None
        return ClientConnected(client_id=UUID(bytes=body))


@dataclass(frozen=True)
class ClientDisconnected:
    TAG: ClassVar[PacketType] = PacketType.CLIENT_DISCONNECTED
    client_id: UUID

    def encode(self) -> str:
        return base64.b64encode(struct.pack("!B", self.TAG.value) + self.client_id.bytes).decode()

    @staticmethod
    def unpack_body(body: bytes) -> ClientDisconnected | None:
        if len(body) != 16:
            return None
        return ClientDisconnected(client_id=UUID(bytes=body))


@dataclass(frozen=True)
class Chat:
    TAG: ClassVar[PacketType] = PacketType.CHAT
    sender_id: UUID
    text: str

    def encode(self) -> str:
        text_bytes = self.text.encode("utf-8")
        raw = struct.pack("!B", self.TAG.value) + self.sender_id.bytes + text_bytes
        return base64.b64encode(raw).decode()

    @staticmethod
    def unpack_body(body: bytes) -> Chat | None:
        if len(body) < 16:
            return None
        raw_id = body[:16]
        sender = UUID(bytes=raw_id)
        text = body[16:].decode("utf-8", "replace")
        return Chat(sender_id=sender, text=text)


# ── Registry & decode ───────────────────────────────────────────────────

Packet = (
    AssignId
    | BoardStateWire
    | MoveRequest
    | MoveResult
    | GameStart
    | ClientConnected
    | ClientDisconnected
    | Chat
    | LobbyUpdate
    | GameOver
    | Join
)

_REGISTRY: dict[PacketType, type[PacketProto]] = {
    PacketType.ASSIGN_ID: AssignId,
    PacketType.BOARD_STATE: BoardStateWire,
    PacketType.MOVE_REQUEST: MoveRequest,
    PacketType.MOVE_RESULT: MoveResult,
    PacketType.GAME_START: GameStart,
    PacketType.CLIENT_CONNECTED: ClientConnected,
    PacketType.CLIENT_DISCONNECTED: ClientDisconnected,
    PacketType.CHAT: Chat,
    PacketType.LOBBY_UPDATE: LobbyUpdate,
    PacketType.GAME_OVER: GameOver,
    PacketType.JOIN: Join,
}


def decode(data: bytes) -> PacketProto | None:
    try:
        raw = base64.b64decode(data, validate=True)
    except Exception:
        return None
    if len(raw) < 1:
        return None
    try:
        packet_type = PacketType(raw[0])
    except ValueError:
        return None
    body = raw[1:]
    cls = _REGISTRY.get(packet_type)
    if cls is None:
        return None
    return cls.unpack_body(body)
