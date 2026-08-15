from __future__ import annotations

import logging
from typing import Unpack

import ajishio as aj

from demo_projects.moonlapse.shared import entities

log = logging.getLogger("moonlapse.world")


class World(aj.GameObject):
    """Manages all game entities. Server-authoritative.

    Receives spawn/destroy/snapshot packets from server and updates
    the entity registry. Each entity is its own aj.GameObject.
    """

    def __init__(
        self,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(**kwargs)
        self.entities: dict[int, entities.Entity] = {}

    def spawn_entity(self, entity: entities.Entity) -> None:
        self.entities[entity.entity_id] = entity

    def destroy_entity(self, entity_id: int) -> None:
        entity = self.entities.pop(entity_id, None)
        if entity is not None:
            aj.instance_destroy(entity)
            log.debug(f"destroyed entity {entity_id}")
