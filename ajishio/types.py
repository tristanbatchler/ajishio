from typing import Protocol, TypedDict, runtime_checkable
from collections.abc import Sequence
from uuid import UUID
from pygame import Surface
from dataclasses import dataclass


@dataclass
class CollisionMask:
    bbleft: float = 0
    bbtop: float = 0
    bbright: float = 0
    bbbottom: float = 0


@dataclass
class GameSprite:
    images: Sequence[Surface]
    width: int
    height: int
    x_offset: float = 0.0
    y_offset: float = 0.0


class Entity(TypedDict):
    x: float
    y: float
    iid: str
    width: int
    height: int
    sprite_index: GameSprite | None
    collision_mask: CollisionMask | None
    customFields: dict[str, object]


@dataclass
class GameLevel:
    tilemaps: dict[str, list[list[bool]]]
    tile_sizes: dict[str, tuple[int, int]]
    background_surfaces: dict[str, Surface]
    level_size: tuple[int, int]
    entities: dict[str, Sequence[Entity]]


class IGameObject(Protocol):
    persistent: bool
    id: UUID
    x: float
    y: float
    sprite_index: GameSprite | None
    image_index: int
    image_speed: float
    image_xscale: float
    image_yscale: float
    collision_mask: CollisionMask | None
    depth: int
    iid: str | None
    width: float
    height: float
    custom_fields: dict[str, object]

    @property
    def sprite_width(self) -> int: ...

    @property
    def sprite_height(self) -> int: ...

    @classmethod
    def create_from_entity(cls, entity: Entity) -> IGameObject: ...

    def step(self) -> None: ...

    def draw(self) -> None: ...

    def on_game_end(self) -> None: ...

    def place_meeting(
        self, x: float, y: float, obj: IGameObject | type[IGameObject] | UUID
    ) -> IGameObject | None: ...
