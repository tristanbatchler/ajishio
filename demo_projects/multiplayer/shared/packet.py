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
        case MessageType.PLAYER_X_INPUT:
            return PlayerXInputPacket.unpack(body)
        case MessageType.PLAYER_JUMP:
            return PlayerJumpPacket.unpack(body)
        case MessageType.OTHER_PLAYER_POSITION:
            return OtherPlayerPositionPacket.unpack(body)
        case MessageType.CONNECTION_REQUEST:
            return ConnectionRequestPacket.unpack(body)
        case MessageType.PLAYER_DISCONNECT:
            return PlayerDisconnectPacket.unpack(body)
        case MessageType.POSITION_SYNC_REQUEST:
            return PositionSyncRequestPacket.unpack(body)
        case MessageType.POSITION_SYNC_RESPONSE:
            return PositionSyncResponsePacket.unpack(body)
        case _:
            raise ValueError("Invalid packet type")

class MessageType(enum.Enum):
    PLAYER_POSITION = 0
    PLAYER_ID = 1
    PLAYER_X_INPUT = 2
    PLAYER_JUMP = 3
    OTHER_PLAYER_POSITION = 4
    CONNECTION_REQUEST = 5
    PLAYER_DISCONNECT = 6
    POSITION_SYNC_REQUEST = 7
    POSITION_SYNC_RESPONSE = 8

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
    
class PlayerXInputPacket(Packet):
    def __init__(self, player_id: UUID, x_input: int) -> None:
        super().__init__(MessageType.PLAYER_X_INPUT)
        self.player_id = player_id
        self.x_input = x_input
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!16sb', self.player_id.bytes, self.x_input)
    
    @staticmethod
    def unpack(data: bytes) -> PlayerXInputPacket:
        player_id, x_input = struct.unpack('!16sb', data)
        return PlayerXInputPacket(UUID(bytes=player_id), x_input)

class PlayerJumpPacket(Packet):
    def __init__(self, player_id: UUID) -> None:
        super().__init__(MessageType.PLAYER_JUMP)
        self.player_id = player_id
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!16s', self.player_id.bytes)
    
    @staticmethod
    def unpack(data: bytes) -> PlayerJumpPacket:
        player_id = struct.unpack('!16s', data)[0]
        return PlayerJumpPacket(UUID(bytes=player_id))

class ConnectionRequestPacket(Packet):
    def __init__(self) -> None:
        super().__init__(MessageType.CONNECTION_REQUEST)
        
    def pack(self) -> bytes:
        return self.header

    @staticmethod
    def unpack(_) -> ConnectionRequestPacket:
        return ConnectionRequestPacket()
    
class PlayerDisconnectPacket(Packet):
    def __init__(self, player_id: UUID) -> None:
        super().__init__(MessageType.PLAYER_DISCONNECT)
        self.player_id = player_id
        
    def pack(self) -> bytes:
        return self.header + struct.pack('!16s', self.player_id.bytes)
    
    @staticmethod
    def unpack(data: bytes) -> PlayerDisconnectPacket:
        player_id = struct.unpack('!16s', data)[0]
        return PlayerDisconnectPacket(UUID(bytes=player_id))
    
class PositionSyncRequestPacket(Packet):
    def __init__(self) -> None:
        super().__init__(MessageType.POSITION_SYNC_REQUEST)

    def pack(self) -> bytes:
        return self.header
    
    @staticmethod
    def unpack(_) -> PositionSyncRequestPacket:
        return PositionSyncRequestPacket()
    
class PositionSyncResponsePacket(Packet):
    def __init__(self, player_id: UUID, x: float, y: float) -> None:
        super().__init__(MessageType.POSITION_SYNC_RESPONSE)
        self.player_id = player_id
        self.x = x
        self.y = y

    def pack(self) -> bytes:
        return self.header + struct.pack('!16sff', self.player_id.bytes, self.x, self.y)
    
    @staticmethod
    def unpack(data: bytes) -> PositionSyncResponsePacket:
        player_id, x, y = struct.unpack('!16sff', data)
        return PositionSyncResponsePacket(UUID(bytes=player_id), x, y)