from __future__ import annotations
import enum
from abc import ABC, abstractmethod
import struct
from uuid import UUID

def unpack(data: bytes) -> Packet:
    header_byte, body = data[0], data[1:]
    match MessageType(header_byte):
        case MessageType.PLAYER_POSITION:
            return PlayerPositionPacket.unpack(body)
        case MessageType.PLAYER_ID:
            return PlayerIdPacket.unpack(body)
        case MessageType.PLAYER_INPUT:
            return PlayerInputPacket.unpack(body)
        case MessageType.OTHER_PLAYER_POSITION:
            return OtherPlayerPositionPacket.unpack(body)
        case MessageType.CONNECTION_REQUEST:
            return ConnectionRequestPacket.unpack(body)
        case _:
            raise ValueError("Invalid packet type")

class MessageType(enum.Enum):
    PLAYER_POSITION = 0
    PLAYER_ID = 1
    PLAYER_INPUT = 2
    OTHER_PLAYER_POSITION = 3
    CONNECTION_REQUEST = 4

class Packet(ABC):
    def __init__(self, message_type: MessageType) -> None:
        self.message_type = message_type
        self.header = struct.pack('!B', self.message_type.value)

    @abstractmethod   
    def pack(self) -> bytes:
        pass
            
class PlayerPositionPacket(Packet):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(MessageType.PLAYER_POSITION)
        self.x = x
        self.y = y
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!ff', self.x, self.y)
    
    @staticmethod
    def unpack(data: bytes) -> PlayerPositionPacket:
        x, y = struct.unpack('!ff', data)
        return PlayerPositionPacket(x, y)

class PlayerIdPacket(Packet):
    def __init__(self, player_id: UUID) -> None:
        super().__init__(MessageType.PLAYER_ID)
        self.player_id = player_id
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!16s', self.player_id.bytes)
    
    @staticmethod
    def unpack(data: bytes) -> PlayerIdPacket:
        player_id = struct.unpack('!16s', data)[0]
        return PlayerIdPacket(UUID(bytes=player_id))
    
class OtherPlayerPositionPacket(Packet):
    def __init__(self, player_id: UUID, x: float, y: float) -> None:
        super().__init__(MessageType.OTHER_PLAYER_POSITION)
        self.player_id = player_id
        self.x = x
        self.y = y
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!16sff', self.player_id.bytes, self.x, self.y)
    
    @staticmethod
    def unpack(data: bytes) -> OtherPlayerPositionPacket:
        player_id, x, y = struct.unpack('!16sff', data)
        return OtherPlayerPositionPacket(UUID(bytes=player_id), x, y)
    
class PlayerInputPacket(Packet):
    def __init__(self, player_id: UUID, x: int, y: int) -> None:
        super().__init__(MessageType.PLAYER_INPUT)
        self.player_id = player_id
        self.x = x
        self.y = y
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!16sbb', self.player_id.bytes, self.x, self.y)
    
    @staticmethod
    def unpack(data: bytes) -> PlayerInputPacket:
        player_id, x, y = struct.unpack('!16sbb', data)
        return PlayerInputPacket(UUID(bytes=player_id), x, y)

class ConnectionRequestPacket(Packet):
    def __init__(self) -> None:
        super().__init__(MessageType.CONNECTION_REQUEST)
        
    def pack(self) -> bytes:
        return self.header

    @staticmethod
    def unpack(_) -> ConnectionRequestPacket:
        return ConnectionRequestPacket()