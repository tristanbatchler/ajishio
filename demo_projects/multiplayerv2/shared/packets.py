"""Binary packet protocol for the multiplayerv2 chatroom.

Wire format
-----------
Every packet is a single WebSocket frame containing a **base64-encoded**
binary blob.  Base64 is used because ``GameNetClient.send()`` accepts
``str`` only, and the ``Transport`` inbox round-trips through UTF-8 —
raw binary would be mangled.

The underlying binary layout is:

    [1 byte type tag] [N bytes body]

The type tag is a ``PacketType`` enum value.  The body format varies per
packet and is documented on each class.

Sender identity
---------------
Sender IDs are 128-bit UUIDs, packed as 16 raw bytes (``!16s``).

Extensibility
-------------
To add a new packet (e.g. Whisper, Poke):

1. Add an entry to ``PacketType``.
2. Create a frozen dataclass with ``encode() -> str`` and
   ``@staticmethod unpack_body(body: bytes) -> Self | None``.
3. Register it in ``_REGISTRY``.
4. Done — ``decode()`` will dispatch to it automatically.
"""

from __future__ import annotations

import base64
import enum
import struct
from dataclasses import dataclass
from typing import ClassVar, Protocol, cast
from uuid import UUID


# ---------------------------------------------------------------------------
# Packet type tag
# ---------------------------------------------------------------------------


class PacketType(enum.IntEnum):
    """Single-byte discriminator written at the start of every packet."""

    ASSIGN_ID = 0
    CHAT = 1
    PING = 2
    PONG = 3
    CLIENT_CONNECTED = 4
    CLIENT_DISCONNECTED = 5


# ---------------------------------------------------------------------------
# Packet protocol (structural typing for the registry)
# ---------------------------------------------------------------------------


class PacketProto(Protocol):
    """Structural interface every concrete packet must satisfy."""

    TAG: ClassVar[PacketType]

    def encode(self) -> str: ...

    @staticmethod
    def unpack_body(body: bytes) -> "Packet | None": ...


# ---------------------------------------------------------------------------
# Concrete packets
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssignId:
    """Server → client.  First packet after connection.

    Body: ``!16s`` — the 128-bit UUID assigned to this client.
    """

    TAG: ClassVar[PacketType] = PacketType.ASSIGN_ID

    sender_id: UUID

    def encode(self) -> str:
        raw = struct.pack("!B16s", self.TAG, self.sender_id.bytes)
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def unpack_body(body: bytes) -> AssignId | None:
        if len(body) != 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body)[0])
        return AssignId(sender_id=UUID(bytes=raw_id))


@dataclass(frozen=True)
class Chat:
    """Chat message.  Sent by clients, broadcast by the server.

    Body: ``!16s`` sender_id + variable-length UTF-8 text.
    """

    TAG: ClassVar[PacketType] = PacketType.CHAT

    sender_id: UUID
    text: str

    def encode(self) -> str:
        text_bytes = self.text.encode("utf-8")
        raw = struct.pack("!B16s", self.TAG, self.sender_id.bytes) + text_bytes
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def unpack_body(body: bytes) -> Chat | None:
        if len(body) < 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body[:16])[0])
        text = body[16:].decode("utf-8", "replace")
        return Chat(sender_id=UUID(bytes=raw_id), text=text)


@dataclass(frozen=True)
class Ping:
    """Client → server.  Requests a ``Pong`` echo.

    Body: ``!16sI`` — sender_id (UUID) + 32-bit payload tag.
    The tag is an arbitrary value the client picks so it can match the
    response; it is NOT an absolute timestamp.
    """

    TAG: ClassVar[PacketType] = PacketType.PING

    sender_id: UUID
    token: int

    def encode(self) -> str:
        raw = struct.pack("!B16sI", self.TAG, self.sender_id.bytes, self.token)
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def unpack_body(body: bytes) -> Ping | None:
        if len(body) != 20:
            return None
        fields = struct.unpack("!16sI", body)
        raw_id = cast(bytes, fields[0])
        token = cast(int, fields[1])
        return Ping(sender_id=UUID(bytes=raw_id), token=token)


@dataclass(frozen=True)
class Pong:
    """Server → client.  Echo of a ``Ping``.

    Body: ``!I`` — the same 32-bit token from the original Ping.
    """

    TAG: ClassVar[PacketType] = PacketType.PONG

    token: int

    def encode(self) -> str:
        raw = struct.pack("!BI", self.TAG, self.token)
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def unpack_body(body: bytes) -> Pong | None:
        if len(body) != 4:
            return None
        token = cast(int, struct.unpack("!I", body)[0])
        return Pong(token=token)


@dataclass(frozen=True)
class ClientConnected:
    """Server → all clients.  Broadcast when a new client joins.

    Body: ``!16s`` — the UUID of the client that just connected.
    """

    TAG: ClassVar[PacketType] = PacketType.CLIENT_CONNECTED

    client_id: UUID

    def encode(self) -> str:
        raw = struct.pack("!B16s", self.TAG, self.client_id.bytes)
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def unpack_body(body: bytes) -> ClientConnected | None:
        if len(body) != 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body)[0])
        return ClientConnected(client_id=UUID(bytes=raw_id))


@dataclass(frozen=True)
class ClientDisconnected:
    """Server → all clients.  Broadcast when a client leaves.

    Body: ``!16s`` — the UUID of the client that disconnected.
    """

    TAG: ClassVar[PacketType] = PacketType.CLIENT_DISCONNECTED

    client_id: UUID

    def encode(self) -> str:
        raw = struct.pack("!B16s", self.TAG, self.client_id.bytes)
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def unpack_body(body: bytes) -> ClientDisconnected | None:
        if len(body) != 16:
            return None
        raw_id = cast(bytes, struct.unpack("!16s", body)[0])
        return ClientDisconnected(client_id=UUID(bytes=raw_id))


# ---------------------------------------------------------------------------
# Union type + registry
# ---------------------------------------------------------------------------

Packet = AssignId | Chat | Ping | Pong | ClientConnected | ClientDisconnected

_REGISTRY: dict[
    int,
    type[AssignId]
    | type[Chat]
    | type[Ping]
    | type[Pong]
    | type[ClientConnected]
    | type[ClientDisconnected],
] = {
    PacketType.ASSIGN_ID: AssignId,
    PacketType.CHAT: Chat,
    PacketType.PING: Ping,
    PacketType.PONG: Pong,
    PacketType.CLIENT_CONNECTED: ClientConnected,
    PacketType.CLIENT_DISCONNECTED: ClientDisconnected,
}


# ---------------------------------------------------------------------------
# Top-level decode
# ---------------------------------------------------------------------------


def decode(data: bytes) -> Packet | None:
    """Decode a raw ``bytes`` value (from ``GameNetClient.recv()``) into a
    typed ``Packet``, or ``None`` on any error.  Never raises.
    """
    try:
        raw = base64.b64decode(data)
    except Exception:
        return None

    if len(raw) < 1:
        return None

    tag = raw[0]
    body = raw[1:]

    cls = _REGISTRY.get(tag)
    if cls is None:
        return None

    return cls.unpack_body(body)
