from __future__ import annotations
from typing import Unpack, override
from ajishio.types import (
    CustomFields,
    GameSprite,
    CollisionMask,
    IGameObject,
    Entity,
    GameObjectKwargs,
)
from uuid import uuid4, UUID
import ajishio._context as _ctx


class GameObject(IGameObject):
    persistent: bool = False

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[GameObjectKwargs],
    ) -> None:
        self.id: UUID = uuid4()
        self.x: float = x
        self.y: float = y
        self.sprite_index: GameSprite | None = kwargs.get("sprite_index")
        self.image_index: int = 0
        self.image_speed: float = 0
        self.image_xscale: float = 1.0
        self.image_yscale: float = 1.0
        self.collision_mask: CollisionMask | None = kwargs.get("collision_mask")
        self.depth: int = 0
        self._last_image_update: float = 0

        self.iid: str | None = kwargs.get("iid")
        self.width: float = kwargs.get("width") or 0
        self.height: float = kwargs.get("height") or 0
        custom_fields = kwargs.get("customFields")
        self.custom_fields: CustomFields = custom_fields if custom_fields is not None else {}

        _ctx.engine.add_object(self)

    @property
    @override
    def sprite_width(self) -> int:
        if self.sprite_index is None:
            return 0
        return self.sprite_index.width

    @property
    @override
    def sprite_height(self) -> int:
        if self.sprite_index is None:
            return 0
        return self.sprite_index.height

    @classmethod
    @override
    def create_from_entity(cls, entity: Entity) -> IGameObject:
        return cls(**entity)

    @override
    def step(self) -> None:
        if self.sprite_index is not None:
            self._last_image_update += _ctx.engine.delta_time
            if (
                self.image_speed > 0
                and len(self.sprite_index.images) > 1
                and self._last_image_update > 1 / self.image_speed
            ):
                self._last_image_update = 0
                self.image_index = (self.image_index + 1) % len(self.sprite_index.images)

    @override
    def draw(self) -> None:
        if self.sprite_index is not None:
            _ctx.engine.renderer.draw_sprite(
                self.x,
                self.y,
                self.sprite_index,
                self.image_index,
                x_scale=self.image_xscale,
                y_scale=self.image_yscale,
            )

    @override
    def on_game_end(self) -> None:
        pass

    @override
    def place_meeting(
        self,
        x: float,
        y: float,
        obj: IGameObject | type[IGameObject] | UUID,  # FIXME: shouldn't this be `str`?
    ) -> IGameObject | None:
        """
        With this function you can check a position for a collision with another instance or all
        instances of an object using the collision mask of the instance that runs the code for the
        check. When you use this you are effectively asking Ajishio to move the instance to the
        new position, check for a collision, move back and tell you if a collision was found or not.

        This function will return the unique instance id of the object being collided. This function
        will return `None` if no collision occurs, or the exact instance found if a collision does
        occur.
        """
        # Check cheapest cases first to avoid the expensive runtime Protocol
        # Type branch: quadtree
        if isinstance(obj, type):
            # Compute the AABB of self at the hypothetical position (x, y)
            s_msk = self.collision_mask
            if s_msk is None:
                return None
            temp_left = x + s_msk.bbleft
            temp_top = y + s_msk.bbtop
            temp_right = x + s_msk.bbright
            temp_bottom = y + s_msk.bbbottom

            # Get candidates from engine's quadtree
            candidates = _ctx.engine.collision_rectangle_list(
                temp_left, temp_top, temp_right, temp_bottom
            )

            for g_o in candidates:
                if g_o is self:
                    continue
                if not isinstance(g_o, obj):
                    continue
                o_msk = g_o.collision_mask
                if o_msk is None:
                    continue
                # Precise AABB check
                if (
                    temp_left < g_o.x + o_msk.bbright
                    and temp_right > g_o.x + o_msk.bbleft
                    and temp_top < g_o.y + o_msk.bbbottom
                    and temp_bottom > g_o.y + o_msk.bbtop
                ):
                    return g_o
            return None

        # UUID branch
        if isinstance(obj, UUID):
            game_obj = _ctx.engine.get_game_object_by_id(obj)
            if game_obj is None:
                return None
            return self.place_meeting(x, y, game_obj)

        # Concrete instance branch
        if not isinstance(obj, GameObject):
            return None
        o = obj
        s_msk = self.collision_mask
        o_msk = o.collision_mask
        if s_msk is None or o_msk is None:
            return None
        if (
            x + s_msk.bbleft < o.x + o_msk.bbright
            and x + s_msk.bbright > o.x + o_msk.bbleft
            and y + s_msk.bbtop < o.y + o_msk.bbbottom
            and y + s_msk.bbbottom > o.y + o_msk.bbtop
        ):
            return o
        return None

    @override
    def on_destroy(self) -> None:
        pass

    def _get_aabb(self) -> tuple[float, float, float, float] | None:
        msk = self.collision_mask
        if msk is None:
            return None
        return (
            self.x + msk.bbleft,
            self.y + msk.bbtop,
            self.x + msk.bbright,
            self.y + msk.bbbottom,
        )
