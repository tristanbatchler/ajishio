from __future__ import annotations
from ajishio.view import _view
from ajishio.engine import _engine
from ajishio.rendering import _renderer
from ajishio.sprite_loader import GameSprite
from dataclasses import dataclass
from uuid import uuid4, UUID
from typing import Any

@dataclass
class CollisionMask:
    bbleft: float = 0
    bbtop: float = 0
    bbright: float = 0
    bbbottom: float = 0

class GameObject:
    def __init__(self, x: float = 0, y: float = 0, sprite_index: GameSprite | None = None, collision_mask: CollisionMask | None = None, *args, **kwargs) -> None:
        self.id: UUID = uuid4()
        self.x: float = x
        self.y: float = y
        self.sprite_index: GameSprite | None = None
        self.image_index: int = 0
        self.image_speed: float = 0
        self.collision_mask: CollisionMask | None = collision_mask
        self._last_image_update: float = 0
        self.persistent: bool = False
        
        self.iid: str = kwargs.get("iid", None)
        self.width: float = kwargs.get("width", 0)
        self.height: float = kwargs.get("height", 0)
        self.custom_fields: dict[str, Any] = kwargs.get("customFields", {})

        _engine.add_object(self)

    @property
    def sprite_width(self) -> int:
        if self.sprite_index is None:
            return 0
        return self.sprite_index.width
    
    @property
    def sprite_height(self) -> int:
        if self.sprite_index is None:
            return 0
        return self.sprite_index.height

    def step(self) -> None:
        if self.sprite_index is not None:
            self._last_image_update += _engine.delta_time
            if self.image_speed > 0 and len(self.sprite_index.images) > 1 and self._last_image_update > _engine.room_speed / self.image_speed:
                self._last_image_update = 0
                self.image_index = (self.image_index + 1) % len(self.sprite_index.images)

    def draw(self) -> None:
        if self.sprite_index is not None:
            _renderer.draw_sprite(self.x, self.y, self.sprite_index, self.image_index)

    def handle_input(self) -> None:
        pass

    def place_meeting(self, x: float, y: float, obj: GameObject | type[GameObject] | UUID) -> GameObject | None:
        if isinstance(obj, GameObject):
            o: GameObject = obj
            s_msk: CollisionMask | None = self.collision_mask
            o_msk: CollisionMask | None = o.collision_mask
            
            if s_msk is None or o_msk is None:
                return None

            if (x + s_msk.bbleft < o.x + o_msk.bbright and
                    x + s_msk.bbright > o.x + o_msk.bbleft and
                    y + s_msk.bbtop < o.y + o_msk.bbbottom and
                    y + s_msk.bbbottom > o.y + o_msk.bbtop):
                return o
            return None

        elif isinstance(obj, UUID):
            obj = _engine._game_objects[obj]
            return self.place_meeting(x, y, obj)
        
        elif issubclass(obj, GameObject):
            for g_o in _engine._game_objects.values():
                if isinstance(g_o, obj):
                    if self.place_meeting(x, y, g_o):
                        return g_o
            return None
        
        else:
            raise TypeError("Invalid type for obj")