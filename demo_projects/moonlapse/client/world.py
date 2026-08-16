from __future__ import annotations

import logging
from typing import Unpack

import ajishio as aj

from demo_projects.moonlapse.shared import entities

log = logging.getLogger("moonlapse.world")


class World(aj.GameObject):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.entities: dict[int, entities.Entity] = {}

    def spawn_entity(self, entity: entities.Entity) -> None:
        self.entities[entity.entity_id] = entity

    def destroy_entity(self, entity_id: int) -> None:
        entity = self.entities.pop(entity_id, None)
        if entity is not None:
            aj.instance_destroy(entity)
            log.debug(f"destroyed entity {entity_id}")
