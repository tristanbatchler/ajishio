from __future__ import annotations
import ajishio as aj
from abc import ABC
from typing import Unpack, ClassVar, override, final
from demo_projects.moonlapse.shared.sprites import spritesheet, SpritesheetIndex

from enum import IntEnum, auto


class EntityType(IntEnum):
    ACTOR = auto()
    TREE = auto()
    ORE = auto()
    FISH = auto()


class Entity(aj.GameObject, ABC):
    TYPE: ClassVar[EntityType]

    def __init__(
        self,
        entity_id: int,
        name: str,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.entity_id: int = entity_id
        self.name: str = name
        self.sprite_index: aj.GameSprite | None = spritesheet


@final
class Actor(Entity):
    TYPE: ClassVar[EntityType] = EntityType.ACTOR

    def __init__(self, entity_id: int, name: str, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(entity_id, name, x, y, **kwargs)
        self.image_index = SpritesheetIndex.MAN_UNARMED

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_text(self.x, self.y, self.name, aj.c_fuchsia)


class Resource(Entity, ABC):
    def __init__(
        self,
        entity_id: int,
        level: int,
        name: str,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(entity_id, name, x, y, **kwargs)
        self.level: int = level


class Tree(Resource):
    TYPE: ClassVar[EntityType] = EntityType.TREE


@final
class RegularTree(Tree):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(entity_id=entity_id, level=1, name="Tree", x=x, y=y, **kwargs)
        self.image_index = SpritesheetIndex.TREE_NORMAL


@final
class OakTree(Tree):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=2, name="Oak Tree", x=x, y=y, **kwargs
        )
        self.image_index = SpritesheetIndex.TREE_OAK


@final
class WillowTree(Tree):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=3, name="Willow Tree", x=x, y=y, **kwargs
        )
        self.image_index = SpritesheetIndex.TREE_WILLOW


class Ore(Resource):
    TYPE: ClassVar[EntityType] = EntityType.ORE


@final
class IronOre(Ore):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=1, name="Iron Ore", x=x, y=y, **kwargs
        )


@final
class GoldOre(Ore):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=2, name="Gold Ore", x=x, y=y, **kwargs
        )


@final
class DiamondOre(Ore):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=3, name="Diamond Ore", x=x, y=y, **kwargs
        )


class Fish(Resource):
    TYPE: ClassVar[EntityType] = EntityType.FISH


@final
class Shrimp(Fish):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=1, name="Shrimp", x=x, y=y, **kwargs
        )


@final
class Salmon(Fish):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(
            entity_id=entity_id, level=2, name="Salmon", x=x, y=y, **kwargs
        )


@final
class Tuna(Fish):
    def __init__(
        self,
        entity_id: int,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(entity_id=entity_id, level=3, name="Tuna", x=x, y=y, **kwargs)
