from __future__ import annotations
from abc import ABC
from typing import Unpack, ClassVar, override
import ajishio as aj

from enum import IntEnum, auto


class EntityType(IntEnum):
    ACTOR = auto()
    TREE = auto()
    ORE = auto()
    FISH = auto()


class Entity(aj.GameObject, ABC):
    TYPE: ClassVar[EntityType]

    _next_id: ClassVar[int] = 0

    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        Entity._next_id += 1
        self.entity_id: int = Entity._next_id


class NamedEntity(Entity, ABC):
    def __init__(
        self,
        name: str,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.name: str = name


class Actor(NamedEntity):
    TYPE: ClassVar[EntityType] = EntityType.ACTOR

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_text(self.x, self.y, self.name, aj.c_fuchsia)


class Resource(NamedEntity, ABC):
    def __init__(
        self,
        level: int,
        name: str,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(name, x, y, **kwargs)
        self.level: int = level


class Tree(Resource):
    TYPE: ClassVar[EntityType] = EntityType.TREE


class RegularTree(Tree):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=1, name="Tree", x=x, y=y, **kwargs)


class OakTree(Tree):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=2, name="Oak Tree", x=x, y=y, **kwargs)


class WillowTree(Tree):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=3, name="Willow Tree", x=x, y=y, **kwargs)


class Ore(Resource):
    TYPE: ClassVar[EntityType] = EntityType.ORE


class IronOre(Ore):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=1, name="Iron Ore", x=x, y=y, **kwargs)


class GoldOre(Ore):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=2, name="Gold Ore", x=x, y=y, **kwargs)


class DiamondOre(Ore):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=3, name="Diamond Ore", x=x, y=y, **kwargs)


class Fish(Resource):
    TYPE: ClassVar[EntityType] = EntityType.FISH


class Shrimp(Fish):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=1, name="Shrimp", x=x, y=y, **kwargs)


class Salmon(Fish):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=2, name="Salmon", x=x, y=y, **kwargs)


class Tuna(Fish):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(level=3, name="Tuna", x=x, y=y, **kwargs)
