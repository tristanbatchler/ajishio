from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Callable, ClassVar, override, final, TypeVar
from abc import ABC

from demo_projects.moonlapse.shared.packets.base import Packet
from demo_projects.moonlapse.shared import entities


class ClientboundPacketType(IntEnum):
    CHAT_RESPONSE = auto()
    MOVE_RESPONSE = auto()
    LOGIN_RESPONSE = auto()
    LOGOUT_RESPONSE = auto()
    REGISTER_RESPONSE = auto()
    CLIENT_ID = auto()
    PLAYER_INFO = auto()
    CLIENT_DISCONNECTED = auto()
    MOTD = auto()
    ANNOUNCEMENT = auto()
    PLAYER_CHAT = auto()
    SERVER_ERROR = auto()
    ENTITY_SPAWN = auto()
    ENTITY_DESTROY = auto()
    ENTITY_UPDATE = auto()
    ACTOR_DETAILS = auto()
    TREE_DETAILS = auto()
    ORE_DETAILS = auto()
    FISH_DETAILS = auto()


REGISTRY: dict[ClientboundPacketType, type[ClientboundPacket]] = {}


@dataclass(frozen=True)
class ClientboundPacket(Packet, ABC): ...


T = TypeVar("T", bound=ClientboundPacket)


def register(packet_type: ClientboundPacketType) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        cls.TYPE = packet_type
        REGISTRY[cls.TYPE] = cls
        return cls

    return decorator


@dataclass(frozen=True)
class ClientboundResponsePacket(ClientboundPacket, ABC):
    ok: bool
    err: str | None = None

    @override
    def get_structure(self):
        return (self.ok, self.err or "")


@final
@register(ClientboundPacketType.CHAT_RESPONSE)
@dataclass(frozen=True)
class ChatResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.MOVE_RESPONSE)
@dataclass(frozen=True)
class MoveResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.LOGIN_RESPONSE)
@dataclass(frozen=True)
class LoginResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.LOGOUT_RESPONSE)
@dataclass(frozen=True)
class LogoutResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.REGISTER_RESPONSE)
@dataclass(frozen=True)
class RegisterResponse(ClientboundResponsePacket): ...


@final
@register(ClientboundPacketType.CLIENT_ID)
@dataclass(frozen=True)
class ClientId(ClientboundPacket):
    id: int

    @override
    def get_structure(self):
        return (self.id,)


@final
@register(ClientboundPacketType.PLAYER_INFO)
@dataclass(frozen=True)
class PlayerInfo(ClientboundPacket):
    name: str
    x_pos: int
    y_pos: int

    @override
    def get_structure(self):
        return (self.name, self.x_pos, self.y_pos)


@final
@register(ClientboundPacketType.CLIENT_DISCONNECTED)
@dataclass(frozen=True)
class ClientDisconnected(ClientboundPacket):
    client_id: int
    reason: str | None = None

    @override
    def get_structure(self):
        return (self.client_id, self.reason or "N/A")


@final
@register(ClientboundPacketType.MOTD)
@dataclass(frozen=True)
class Motd(ClientboundPacket):
    motd: str

    @override
    def get_structure(self):
        return (self.motd,)


@final
@register(ClientboundPacketType.ANNOUNCEMENT)
@dataclass(frozen=True)
class Announcement(ClientboundPacket):
    message: str

    @override
    def get_structure(self):
        return (self.message,)


@final
@register(ClientboundPacketType.PLAYER_CHAT)
@dataclass(frozen=True)
class PlayerChat(ClientboundPacket):
    from_client_id: int
    message: str

    @override
    def get_structure(self):
        return (self.from_client_id, self.message)


@final
@register(ClientboundPacketType.SERVER_ERROR)
@dataclass(frozen=True)
class ServerError(ClientboundPacket):
    message: str

    @override
    def get_structure(self):
        return (self.message,)


@dataclass(frozen=True)
class EntityDetails(ClientboundPacket, ABC):
    BASE_FORMAT_STRING: ClassVar[str] = "Iii"
    entity_id: int
    x: int
    y: int

    @override
    def get_structure(self) -> tuple[object, ...]:
        return (self.entity_id, self.x, self.y)

    @staticmethod
    def from_entity(entity: entities.Entity) -> EntityDetails:
        details: EntityDetails | None = None
        match entity:
            case entities.Actor():
                details = ActorDetails(
                    entity_id=entity.entity_id,
                    x=int(entity.x),
                    y=int(entity.y),
                    name=entity.name,
                )
            case entities.Tree():
                details = TreeDetails(
                    entity_id=entity.entity_id,
                    x=int(entity.x),
                    y=int(entity.y),
                    level=entity.level,
                    name=entity.name,
                )
            case entities.Ore():
                details = OreDetails(
                    entity_id=entity.entity_id,
                    x=int(entity.x),
                    y=int(entity.y),
                    level=entity.level,
                    name=entity.name,
                )
            case entities.Fish():
                details = FishDetails(
                    entity_id=entity.entity_id,
                    x=int(entity.x),
                    y=int(entity.y),
                    level=entity.level,
                    name=entity.name,
                )
            case _:
                raise NotImplementedError(
                    f"Entity type {entity.TYPE} does not have an implementation for EntityDetails.from_entity"
                )

        return details


@final
@register(ClientboundPacketType.ACTOR_DETAILS)
@dataclass(frozen=True)
class ActorDetails(EntityDetails):
    name: str

    @override
    def get_structure(self):
        return super().get_structure() + (self.name,)


@dataclass(frozen=True)
class ResourceDetails(EntityDetails, ABC):
    BASE_FORMAT_STRING: ClassVar[str] = EntityDetails.BASE_FORMAT_STRING + "i"
    level: int

    @override
    def get_structure(self) -> tuple[object, ...]:
        return super().get_structure() + (self.level,)


@final
@register(ClientboundPacketType.TREE_DETAILS)
@dataclass(frozen=True)
class TreeDetails(ResourceDetails):
    name: str

    @override
    def get_structure(self):
        return super().get_structure() + (self.name,)


@final
@register(ClientboundPacketType.ORE_DETAILS)
@dataclass(frozen=True)
class OreDetails(ResourceDetails):
    name: str

    @override
    def get_structure(self):
        return super().get_structure() + (self.name,)


@final
@register(ClientboundPacketType.FISH_DETAILS)
@dataclass(frozen=True)
class FishDetails(ResourceDetails):
    name: str

    @override
    def get_structure(self):
        return super().get_structure() + (self.name,)


@final
@register(ClientboundPacketType.ENTITY_SPAWN)
@dataclass(frozen=True)
class EntitySpawn(ClientboundPacket):
    entity_id: int
    entity_type: entities.EntityType
    entity_details_blob: str

    @override
    def get_structure(self):
        return (self.entity_id, self.entity_type, self.entity_details_blob)


@final
@register(ClientboundPacketType.ENTITY_DESTROY)
@dataclass(frozen=True)
class EntityDestroy(ClientboundPacket):
    entity_id: int

    @override
    def get_structure(self):
        return (self.entity_id,)


@final
@register(ClientboundPacketType.ENTITY_UPDATE)
@dataclass(frozen=True)
class EntityUpdate(ClientboundPacket):
    entity_id: int
    entity_details_blob: str

    @override
    def get_structure(self):
        return (self.entity_id, self.entity_details_blob,)
