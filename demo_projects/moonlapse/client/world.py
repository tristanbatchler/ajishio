from __future__ import annotations

import logging
from typing import Unpack, override
from dataclasses import fields

import ajishio as aj

from demo_projects.moonlapse.shared import entities
from demo_projects.moonlapse.shared.packets.clientbound import EntityDetails

logger = logging.getLogger("moonlapse.world")


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
            logger.debug(f"destroyed entity {entity_id}")

    def update_entity(self, entity_id: int, entity_details: EntityDetails):
        entity = self.entities.get(entity_id)
        if entity is None:
            logger.error(f"Can't update entity {entity_id} because it doesn't exist in the world")
            return

        for field in fields(entity_details):
            entity.__setattr__(field.name, entity_details.__getattribute__(field.name))

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_text(10, 10, f"WORLD ({len(self.entities)}) entities")