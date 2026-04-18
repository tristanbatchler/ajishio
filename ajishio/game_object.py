from __future__ import annotations
from ajishio.types import GameSprite, CollisionMask, IGameObject, Entity
from uuid import uuid4, UUID
import ajishio._context as _ctx




class GameObject:
    persistent: bool = False

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        sprite_index: GameSprite | None = None,
        collision_mask: CollisionMask | None = None,
        iid: str | None = None,
        width: float = 0,
        height: float = 0,
        customFields: dict[str, object] | None = None,
        **_: object,
    ) -> None:
        self.id: UUID = uuid4()
        self.x: float = x
        self.y: float = y
        self.sprite_index: GameSprite | None = sprite_index
        self.image_index: int = 0
        self.image_speed: float = 0
        self.image_xscale: float = 1.0
        self.image_yscale: float = 1.0
        self.collision_mask: CollisionMask | None = collision_mask
        self.depth: int = 0
        self._last_image_update: float = 0

        self.iid: str | None = iid
        self.width: float = width
        self.height: float = height
        self.custom_fields: dict[str, object] = customFields if customFields is not None else {}

        _ctx.engine.add_object(self)

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

    @classmethod
    def create_from_entity(cls, entity: Entity) -> IGameObject:
        return cls(**entity)

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

    def draw(self) -> None:
        if self.sprite_index is not None:
            _ctx.engine.renderer.draw_sprite(self.x, self.y, self.sprite_index, self.image_index, x_scale=self.image_xscale, y_scale=self.image_yscale)

    def on_game_end(self) -> None:
        pass

    def place_meeting(
        self, x: float, y: float, obj: IGameObject | type[IGameObject] | UUID
    ) -> IGameObject | None:
        # Check cheapest cases first to avoid the expensive runtime Protocol
        # isinstance check that inspect.getattr_static triggers on IGameObject.
        if isinstance(obj, type):
            for g_o in _ctx.engine.get_game_objects():
                if isinstance(g_o, obj) and self.place_meeting(x, y, g_o):
                    return g_o
            return None

        if isinstance(obj, UUID):
            game_obj = _ctx.engine.get_game_object_by_id(obj)
            if game_obj is None:
                return None
            return self.place_meeting(x, y, game_obj)

        # obj is a concrete game object instance
        o: IGameObject = obj
        s_msk: CollisionMask | None = self.collision_mask
        o_msk: CollisionMask | None = o.collision_mask

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
