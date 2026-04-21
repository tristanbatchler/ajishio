# Project Summary

## ajishio/src/ajishio/_context.py
```python
from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ajishio.engine import Engine

# Set once in ajishio/__init__.py before any game logic runs.
# Internal modules import this module (not the value) so the lookup is always fresh.
# cast(None) is a safe sentinel: type checkers see Engine, runtime sees None until __init__.py runs.
engine: Engine = cast("Engine", cast(object, None))
```

## ajishio/src/ajishio/engine.py
```python
from __future__ import annotations

import asyncio
from collections.abc import Container, Iterable, Callable
from logging import Logger
from typing import TYPE_CHECKING, cast
from uuid import UUID
from ajishio.input import input
from ajishio.view import view
from ajishio.types import CollisionMask, GameLevel, IGameObject
from ajishio.rendering import Renderer, Color
import pygame as pg
import sys
import logging

if TYPE_CHECKING:
    from ajishio.game_sound import GameSound


epsilon: float = 0.00001


class Engine:
    def __init__(self, renderer: Renderer) -> None:
        self.renderer: Renderer = renderer
        self.room_width: float
        self.room_height: float
        self.room_speed: float
        self.room_background_color: pg.Color
        self.room: int = 0
        self.delta_time: float
        self.fps_real: float

        self.room_set_size(view.view_wport[view.view_current], view.view_hport[view.view_current])
        self.game_set_speed(60)
        self.room_set_background(Color(0, 0, 0))

        self._clock: pg.time.Clock = pg.time.Clock()
        self._last_render_time: float = 0
        self._game_objects: dict[UUID, IGameObject] = {}
        self._game_objects_to_destroy: set[IGameObject] = set()
        self._game_objects_to_add: list[IGameObject] = []
        self._game_running: bool = False
        self._object_registry: dict[str, type[IGameObject]] = {}

        self._rooms: list[GameLevel] = []
        self._audio_playing: list[GameSound] = []

        self._logger: Logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

    def set_rooms(self, rooms: list[GameLevel]) -> None:
        self._rooms = rooms

    def register_objects(self, *objects: type[IGameObject]) -> None:
        for obj in objects:
            self._object_registry[obj.__name__] = obj

    def room_goto(self, index: int) -> None:
        # Remove just the non-persistent instances
        for instance in self._game_objects.values():
            if not instance.persistent:
                self.instance_destroy(instance)

        level = self._rooms[index]

        self.room_set_size(*level.level_size)

        # Draw the level
        self.renderer.set_background_images(list(level.background_surfaces.values()))

        # Load the tilemaps
        for layer, tilemap in level.tilemaps.items():
            tile_size: tuple[int, int] = level.tile_sizes[layer]

            for y, row in enumerate(tilemap):
                for x, cell in enumerate(row):
                    if cell:
                        tile_cls = self._object_registry.get(layer)
                        if tile_cls is None:
                            raise ValueError(
                                f"{layer} object not found in registry. Make sure you "
                                + f"have registered it with `aj.register_objects({layer})`"
                            )
                        _ = cast(Callable[..., IGameObject], tile_cls)(
                            x * tile_size[0],
                            y * tile_size[1],
                            width=tile_size[0],
                            height=tile_size[1],
                        )

        # Load the entities
        for entity_type, entities in level.entities.items():
            for entity in entities:
                entity_cls = self._object_registry.get(entity_type)
                if entity_cls is None:
                    self._logger.warning(
                        "%s object not found in registry. Make sure you "
                        + "have registered it with `aj.register_objects(%s)`",
                        entity_type,
                        entity_type,
                    )
                    continue

                if not (self.instance_exists(entity_cls) and entity_cls.persistent):
                    _ = entity_cls.create_from_entity(entity)

        self.room = index

    def room_goto_next(self) -> None:
        self.room_goto(self.room + 1)

    def room_goto_previous(self) -> None:
        self.room_goto(self.room - 1)

    def room_restart(self) -> None:
        self.room_goto(self.room)

    def game_restart(self) -> None:
        for obj in self._game_objects.values():
            self.instance_destroy(obj)
        if len(self._rooms) > 0:
            self.room_goto(0)

    def game_end(self) -> None:
        self._game_running = False
        for obj in self._game_objects.values():
            obj.on_game_end()

    def game_set_speed(self, speed: float) -> None:
        self.room_speed = speed
        if speed != 0:
            self.delta_time = 1 / self.room_speed  # seconds

    def window_set_size(self, w: int, h: int) -> None:
        view.window_set_size(w, h)
        self.renderer.set_screen_size(w, h)
        # viewport was also synced to window by view.window_set_size, so re-create surface
        self.renderer.fit_display()

    def view_set_wport(self, view_idx: int, w: float) -> None:
        view.view_set_wport(view_idx, w)

    def view_set_hport(self, view_idx: int, h: float) -> None:
        view.view_set_hport(view_idx, h)

    def view_set_xport(self, view_idx: int, x: float) -> None:
        view.view_set_xport(view_idx, x)

    def view_set_yport(self, view_idx: int, y: float) -> None:
        view.view_set_yport(view_idx, y)

    def room_set_size(self, w: float, h: float) -> None:
        self.room_width = w
        self.room_height = h

    def room_set_width(self, w: int) -> None:
        self.room_set_size(w, self.room_height)

    def room_set_height(self, h: int) -> None:
        self.room_set_size(self.room_width, h)

    def room_set_background(self, color: pg.Color) -> None:
        self.room_background_color = color

    def audio_play_sound(self, index: GameSound, loop: bool = False, gain: float = 1) -> None:
        self._audio_playing.append(index)
        index.play(loop=loop, gain=gain)

    def audio_is_playing(self, index: GameSound) -> bool:
        return index in self._audio_playing

    def add_object(self, obj: IGameObject) -> None:
        self._game_objects_to_add.append(obj)

    def instance_destroy(self, obj: IGameObject) -> None:
        obj.on_destroy()
        self._game_objects_to_destroy.add(obj)

    def instance_count(self, obj: type[IGameObject]) -> int:
        count: int = 0
        all_objects = list(self._game_objects.values()) + self._game_objects_to_add
        for g_o in all_objects:
            if isinstance(g_o, obj) and g_o not in self._game_objects_to_destroy:
                count += 1
        return count

    def instance_exists(self, obj: type[IGameObject]) -> bool:
        return self.instance_count(obj) > 0

    def instance_find(self, obj: type[IGameObject] | str, n: int = 0) -> IGameObject | None:
        all_objects = list(self._game_objects.values()) + self._game_objects_to_add

        if isinstance(obj, str):
            for g_o in all_objects:
                if g_o.iid == obj and g_o not in self._game_objects_to_destroy:
                    return g_o
            return None

        count: int = 0
        for g_o in all_objects:
            if isinstance(g_o, obj) and g_o not in self._game_objects_to_destroy:
                if count == n:
                    return g_o
                count += 1
        return None

    def instance_position(
        self, x: float, y: float, obj: IGameObject | type[IGameObject] | str
    ) -> IGameObject | None:
        """
        With this function you can check a position for a collision with another instance or all
        instances of an object. When you use this you are checking a single point in the room for an
        instance or an object. This check will be done against the collision mask of the instance
        and will return the unique instance id. This function will return `None` if no collision
        occurs, or the exact instance found if a collision does occur.
        """

        if isinstance(obj, IGameObject):
            if obj in self._game_objects_to_destroy or obj.collision_mask is None:
                return None

            msk = obj.collision_mask
            if (
                obj.x + msk.bbleft <= x <= obj.x + msk.bbright
                and obj.y + msk.bbtop <= y <= obj.y + msk.bbbottom
            ):
                return obj

        if isinstance(obj, str):
            target = self.instance_find(obj)
            if target is None:
                return None
            return self.instance_position(x, y, target)

        if isinstance(obj, type):
            all_objects = list(self._game_objects.values()) + self._game_objects_to_add
            for g_o in all_objects:
                if g_o in self._game_objects_to_destroy or g_o.collision_mask is None:
                    continue

                if isinstance(g_o, obj):
                    msk = g_o.collision_mask
                    if (
                        g_o.x + msk.bbleft <= x <= g_o.x + msk.bbright
                        and g_o.y + msk.bbtop <= y <= g_o.y + msk.bbbottom
                    ):
                        return g_o

        return None

    def collision_rectangle(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        obj: IGameObject | type[IGameObject] | UUID,  # FIXME: Shouldn't this be `str`?
        not_these: Container[IGameObject] | None = None,
    ) -> IGameObject | None:
        """
        This function checks a rectangular area for a collision with the given instance or
        instances of the given object, and returns the first result found.

        You may also choose to supply any special instances that are excluded from collision checks.

        This function will return the unique id of the instance being collided with. If no
        collisions are found, noone is returned.
        """
        if isinstance(obj, type):
            for g_o in self.instances_iterate(obj):
                if self.collision_rectangle(x1, y1, x2, y2, g_o, not_these):
                    return g_o
            return None

        if isinstance(obj, UUID):
            game_obj = self.get_game_object_by_id(obj)
            if game_obj is None:
                return None
            return self.collision_rectangle(x1, y1, x2, y2, game_obj, not_these)

        if not_these is not None and obj in not_these:
            return None

        o = obj
        o_msk: CollisionMask | None = o.collision_mask

        if o_msk is None:
            return None

        if (
            x1 < o.x + o_msk.bbright
            and x2 > o.x + o_msk.bbleft
            and y1 < o.y + o_msk.bbbottom
            and y2 > o.y + o_msk.bbtop
        ):
            return o
        return None

    def game_start(self) -> None:
        if len(self._rooms) > 0:
            self.room_goto(0)

        self._game_running = True
        while self._game_running:
            try:
                input.events += pg.event.get()

                if any(event.type == pg.QUIT for event in input.events):
                    self.game_end()

                self.delta_time = self._clock.tick(self.room_speed) / 1000  # ms to seconds
                self.fps_real = self._clock.get_fps()

                if self.room_speed == 0:
                    continue
                self._last_render_time += self.delta_time
                if self._last_render_time >= 1 / self.room_speed:
                    self._last_render_time %= 1 / self.room_speed
                    self.renderer.fit_display()
                    self.renderer.fill_background_color(self.room_background_color)
                    self.renderer.draw_background_images()

                    self._add_pending_objects()
                    self._free_destroyed_objects()

                    for obj in self._game_objects.values():
                        obj.step()

                    draw_buffer = sorted(
                        self._game_objects.values(),
                        key=lambda obj: obj.depth,
                        reverse=True,
                    )

                    for obj in draw_buffer:
                        obj.draw()

                    # Only clear the input after all objects have had a chance to process it
                    input.prev_events = input.events.copy()
                    input.events.clear()

                    pg.display.update()
                    self.renderer.draw_display()

                self._audio_playing = [
                    audio for audio in self._audio_playing if not audio.is_finished(self.delta_time)
                ]

            except KeyboardInterrupt:
                self._game_running = False

        pg.quit()
        sys.exit()

    async def async_game_start(self) -> None:
        """Async version of game_start for pygbag/WASM compatibility.
        Yields control to the browser event loop every frame."""
        if len(self._rooms) > 0:
            self.room_goto(0)

        self._game_running = True
        while self._game_running:
            try:
                input.events += pg.event.get()

                if any(event.type == pg.QUIT for event in input.events):
                    self.game_end()

                self.delta_time = self._clock.tick(self.room_speed) / 1000
                self.fps_real = self._clock.get_fps()

                if self.room_speed == 0:
                    await asyncio.sleep(0)
                    continue
                self._last_render_time += self.delta_time
                if self._last_render_time >= 1 / self.room_speed:
                    self._last_render_time %= 1 / self.room_speed
                    self.renderer.fit_display()
                    self.renderer.fill_background_color(self.room_background_color)
                    self.renderer.draw_background_images()

                    self._add_pending_objects()
                    self._free_destroyed_objects()

                    for obj in self._game_objects.values():
                        obj.step()

                    draw_buffer = sorted(
                        self._game_objects.values(),
                        key=lambda obj: obj.depth,
                        reverse=True,
                    )

                    for obj in draw_buffer:
                        obj.draw()

                    input.prev_events = input.events.copy()
                    input.events.clear()

                    pg.display.update()
                    self.renderer.draw_display()

                self._audio_playing = [
                    audio for audio in self._audio_playing if not audio.is_finished(self.delta_time)
                ]

            except KeyboardInterrupt:
                self._game_running = False

            await asyncio.sleep(0)

        pg.quit()

    def get_game_objects(self) -> Iterable[IGameObject]:
        return self._game_objects.values()

    def get_game_object_by_id(self, id: UUID) -> IGameObject | None:
        return self._game_objects.get(id)

    def instances_iterate(self, obj: type[IGameObject]) -> Iterable[IGameObject]:
        """
        With this function you can iterate over all instances of an object. This is especially
        useful for doing something to all instances of an object in a loop.
        """
        all_objects = list(self._game_objects.values()) + self._game_objects_to_add
        for g_o in all_objects:
            if g_o in self._game_objects_to_destroy:
                continue
            if isinstance(g_o, obj):
                yield g_o

    @property
    def mouse_x(self) -> float:
        return pg.mouse.get_pos()[0]

    @property
    def mouse_y(self) -> float:
        return pg.mouse.get_pos()[1]

    def _free_destroyed_objects(self) -> None:
        for obj in self._game_objects_to_destroy:
            try:
                _ = self._game_objects.pop(obj.id)
            except KeyError:
                pass
        self._game_objects_to_destroy.clear()

    def _add_pending_objects(self) -> None:
        for obj in self._game_objects_to_add:
            self._game_objects[obj.id] = obj
        self._game_objects_to_add.clear()
```

## ajishio/src/ajishio/game_object.py
```python
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
        # isinstance check that inspect.getattr_static triggers on IGameObject.
        if isinstance(obj, type):
            for g_o in _ctx.engine.instances_iterate(obj):
                if self.place_meeting(x, y, g_o):
                    return g_o
            return None

        if isinstance(obj, UUID):
            game_obj = _ctx.engine.get_game_object_by_id(obj)
            if game_obj is None:
                return None
            return self.place_meeting(x, y, game_obj)

        # obj is a concrete game object instance; all stored objects are GameObjects
        # assert isinstance(obj, GameObject)
        if not isinstance(obj, GameObject):
            return None

        o = obj
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

    @override
    def on_destroy(self) -> None:
        pass
```

## ajishio/src/ajishio/game_sound.py
```python
import pygame as pg


class GameSound:
    def __init__(self, sound: pg.mixer.Sound) -> None:
        self.sound: pg.mixer.Sound = sound
        self.duration_ms: float = sound.get_length() * 1000
        self._time_since_started_playing: float | None = None
        self._looping: bool = False

    def play(self, loop: bool = False, gain: float = 1) -> None:
        self.sound.set_volume(gain)
        _ = self.sound.play(-1 if loop else 0)
        self._looping = loop
        self._time_since_started_playing = 0

    def is_finished(self, delta_time: float) -> bool:
        if self._looping:
            return False
        if self._time_since_started_playing is None:
            return True
        self._time_since_started_playing += delta_time
        if self._time_since_started_playing > self.duration_ms:
            self._time_since_started_playing = None
            self.sound.set_volume(1)
            return True
        return False
```

## ajishio/src/ajishio/__init__.py
```python
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, cast

import pygame as _pg
Color = _pg.Color

import os as _os
import ajishio._context as _ctx
from ajishio.view import view
from ajishio.rendering import Renderer
from ajishio.engine import Engine

# --- Public class / type exports ---
from ajishio.game_object import GameObject
from ajishio.types import (
    GameSprite,
    GameLevel,
    CollisionMask,
    IGameObject,
    Entity,
    CustomFields,
    GameObjectKwargs,
)
from ajishio.game_sound import GameSound

# --- Input ---
from ajishio.input import (
    keyboard_check,
    keyboard_check_pressed,
    keyboard_check_released,
    mouse_check_button,
    mouse_check_button_pressed,
    mouse_check_button_released,
    ord,
    vk_left,
    vk_right,
    vk_up,
    vk_down,
    vk_space,
    vk_escape,
    vk_enter,
    mb_left,
    mb_middle,
    mb_right,
)

# --- Utils ---
from ajishio.utils import (
    lengthdir_x,
    lengthdir_y,
    clamp,
    sign,
    lerp,
    point_distance,
    map_value,
    room_set_caption,
    profile,
)

# --- Rendering: color constants and free functions ---
from ajishio.rendering import (
    c_aqua,
    c_black,
    c_blue,
    c_dkgray,
    c_fuchsia,
    c_gray,
    c_green,
    c_lime,
    c_ltgray,
    c_maroon,
    c_navy,
    c_olive,
    c_orange,
    c_purple,
    c_red,
    c_silver,
    c_teal,
    c_white,
    c_yellow,
    make_color_hsv,
    load_font,
)

# --- Asset loaders ---
from ajishio.sprite_loader import (
    load_aseprite_sprites,
    load_aseprite_sprite,
    sprite_set_offset,
)
from ajishio.sound_loader import load_sounds, load_sound
from ajishio.level_loader import load_ldtk_levels

# --- Singleton instantiation (must happen before any game logic runs) ---
if _os.environ.get("AJISHIO_DOCS"):
    # Documentation mode: use lightweight dummies that won't open a window
    class _Dummy:
        def __getattr__(self, name: str) -> Callable[..., None]:
            return lambda *args, **kwargs: None

    _renderer: Renderer = cast(Renderer, _Dummy())
    _engine: Engine = cast(Engine, _Dummy())
else:
    import pygame as _pg

    _ = _pg.init()
    _renderer = Renderer()
    _engine = Engine(_renderer)


# Populate the lazy context so game_object / game_sound can access the engine.
_ctx.engine = _engine

# --- Rendering: bound methods on the renderer singleton ---
draw_circle = _renderer.draw_circle
draw_rectangle = _renderer.draw_rectangle
draw_line = _renderer.draw_line
draw_text = _renderer.draw_text
draw_sprite = _renderer.draw_sprite
draw_set_font = _renderer.draw_set_font
text_width = _renderer.text_width
text_height = _renderer.text_height

# --- View: bound methods delegated through engine so the renderer stays in sync ---
view_set_wport = _engine.view_set_wport
view_set_hport = _engine.view_set_hport
view_set_xport = _engine.view_set_xport
view_set_yport = _engine.view_set_yport
window_set_size = _engine.window_set_size

# These are mutable dicts — exporting a reference is safe; mutations are shared.
view_xport = view.view_xport
view_yport = view.view_yport
view_wport = view.view_wport
view_hport = view.view_hport

# --- Engine method delegates ---
game_start = _engine.game_start
async_game_start = _engine.async_game_start
game_end = _engine.game_end
game_restart = _engine.game_restart
game_set_speed = _engine.game_set_speed
set_rooms = _engine.set_rooms
register_objects = _engine.register_objects
room_goto = _engine.room_goto
room_goto_next = _engine.room_goto_next
room_goto_previous = _engine.room_goto_previous
room_restart = _engine.room_restart

room_set_size: Callable[[float, float], None] = _engine.room_set_size
"""Sets the size of the room. This does not affect the window size or viewport."""

room_set_width = _engine.room_set_width
room_set_height = _engine.room_set_height
room_set_background = _engine.room_set_background
instance_destroy = _engine.instance_destroy
instance_count = _engine.instance_count
instance_exists = _engine.instance_exists
instance_position = _engine.instance_position
instance_find = _engine.instance_find
instances_iterate = _engine.instances_iterate
collision_rectangle = _engine.collision_rectangle
audio_play_sound = _engine.audio_play_sound
audio_is_playing = _engine.audio_is_playing

# --- Live engine properties (change every frame) ---
_LIVE_ENGINE_ATTRS = frozenset(
    {
        "room_width",
        "room_height",
        "room_speed",
        "room_background_color",
        "delta_time",
        "fps_real",
        "room",
        "mouse_x",
        "mouse_y",
    }
)

_LIVE_VIEW_ATTRS = frozenset(
    {
        "view_current",
        "window_width",
        "window_height",
    }
)


def __getattr__(name: str) -> object:
    if name in _LIVE_ENGINE_ATTRS:
        try:
            return getattr(_engine, name)  # type: ignore[return-value]
        except AttributeError:
            raise AttributeError(f"module 'ajishio' has no attribute {name!r}")
    if name in _LIVE_VIEW_ATTRS:
        return getattr(view, name)  # type: ignore[return-value]
    raise AttributeError(f"module 'ajishio' has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(__all__)


if TYPE_CHECKING:
    import pygame as pg

    room_width: float
    room_height: float
    room_speed: float
    room_background_color: pg.Color
    delta_time: float
    fps_real: float
    room: int

    view_current: int
    window_width: int
    window_height: int
    mouse_x: float
    mouse_y: float


__all__ = [
    # Classes / types
    "GameObject",
    "GameSprite",
    "GameLevel",
    "CollisionMask",
    "IGameObject",
    "Entity",
    "CustomFields",
    "GameObjectKwargs",
    "GameSound",
    "Color",
    # Input
    "keyboard_check",
    "keyboard_check_pressed",
    "keyboard_check_released",
    "mouse_check_button",
    "mouse_check_button_pressed",
    "mouse_check_button_released",
    "ord",
    "vk_left",
    "vk_right",
    "vk_up",
    "vk_down",
    "vk_space",
    "vk_escape",
    "vk_enter",
    "mb_left",
    "mb_middle",
    "mb_right",
    # Utils
    "lengthdir_x",
    "lengthdir_y",
    "clamp",
    "sign",
    "lerp",
    "profile",
    "point_distance",
    "map_value",
    "room_set_caption",
    # Colors
    "c_aqua",
    "c_black",
    "c_blue",
    "c_dkgray",
    "c_fuchsia",
    "c_gray",
    "c_green",
    "c_lime",
    "c_ltgray",
    "c_maroon",
    "c_navy",
    "c_olive",
    "c_orange",
    "c_purple",
    "c_red",
    "c_silver",
    "c_teal",
    "c_white",
    "c_yellow",
    "make_color_hsv",
    "load_font",
    # Drawing
    "draw_circle",
    "draw_rectangle",
    "draw_line",
    "draw_text",
    "draw_sprite",
    "draw_set_font",
    "text_width",
    "text_height",
    # View
    "view_set_wport",
    "view_set_hport",
    "view_set_xport",
    "view_set_yport",
    "window_set_size",
    "view_xport",
    "view_yport",
    "view_wport",
    "view_hport",
    # Loaders
    "load_aseprite_sprites",
    "load_aseprite_sprite",
    "sprite_set_offset",
    "load_sounds",
    "load_sound",
    "load_ldtk_levels",
    # Engine methods
    "game_start",
    "async_game_start",
    "game_end",
    "game_restart",
    "game_set_speed",
    "set_rooms",
    "register_objects",
    "room_goto",
    "room_goto_next",
    "room_goto_previous",
    "room_restart",
    "room_set_size",
    "room_set_width",
    "room_set_height",
    "room_set_background",
    "instance_destroy",
    "instance_count",
    "instance_exists",
    "instance_position",
    "instance_find",
    "instances_iterate",
    "collision_rectangle",
    "audio_play_sound",
    "audio_is_playing",
    # Live properties (resolved via __getattr__)
    "room_width",
    "room_height",
    "room_speed",
    "room_background_color",
    "delta_time",
    "fps_real",
    "room",
    "view_current",
    "window_width",
    "window_height",
]
```

## ajishio/src/ajishio/input.py
```python
from __future__ import annotations
import pygame as pg


class QuitInterrupt(Exception):
    pass


class Input:
    def __init__(self) -> None:
        self.prev_events: list[pg.event.Event] | None = None
        self.events: list[pg.event.Event] = []


input = Input()


def keyboard_check_pressed(key: int) -> bool:
    pressed_now: bool = any(event.type == pg.KEYDOWN and event.key == key for event in input.events)
    if input.prev_events is None:
        return pressed_now
    pressed_before: bool = any(
        event.type == pg.KEYDOWN and event.key == key for event in input.prev_events
    )
    return pressed_now and not pressed_before


def mouse_check_button_pressed(mb: int) -> bool:
    pressed_now: bool = any(
        event.type == pg.MOUSEBUTTONDOWN and event.button == mb for event in input.events
    )
    if input.prev_events is None:
        return pressed_now
    pressed_before: bool = any(
        event.type == pg.MOUSEBUTTONDOWN and event.button == mb for event in input.prev_events
    )
    return pressed_now and not pressed_before


def keyboard_check_released(key: int) -> bool:
    return any(event.type == pg.KEYUP and event.key == key for event in input.events)


def mouse_check_button_released(mb: int) -> bool:
    return any(event.type == pg.MOUSEBUTTONUP and event.button == mb for event in input.events)


def keyboard_check(key: int) -> bool:
    return pg.key.get_pressed()[key]


def mouse_check_button(mb: int) -> bool:
    pressed = pg.mouse.get_pressed()

    if mb in (mb_left, mb_middle, mb_right):
        return pressed[mb - 1]

    return False


def ord(char: str) -> int:
    return pg.key.key_code(char)


vk_left: int = pg.K_LEFT
vk_right: int = pg.K_RIGHT
vk_up: int = pg.K_UP
vk_down: int = pg.K_DOWN
vk_space: int = pg.K_SPACE
vk_escape: int = pg.K_ESCAPE
vk_enter: int = pg.K_RETURN

mb_left: int = 1
mb_middle: int = 2
mb_right: int = 3
```

## ajishio/src/ajishio/level_loader.py
```python
from collections.abc import Sequence
import csv
import json
from pathlib import Path
from typing import TypedDict, cast

import pygame as pg

from ajishio.utils import remove_ext
from ajishio.types import Entity, GameLevel

type EntitiesByType = dict[str, Sequence[Entity]]


class RawLevelInfo(TypedDict):
    width: int
    height: int
    layers: list[str]
    entities: EntitiesByType


def load_ldtk_levels(ldtk_super_simple_export_simplified_path: Path) -> list[GameLevel]:
    alphabetical_level_dirs: list[Path] = sorted(
        ldtk_super_simple_export_simplified_path.iterdir()
    )
    return [load_ldtk(level_dir) for level_dir in alphabetical_level_dirs]


def load_ldtk(level_dir: Path) -> GameLevel:
    tilemaps: dict[str, list[list[bool]]] = {}
    tile_sizes: dict[str, tuple[int, int]] = {}
    background_surfaces: dict[str, pg.Surface] = {}

    level_info: RawLevelInfo = cast(
        RawLevelInfo,
        json.loads((level_dir / "data.json").read_text()),
    )

    # Get the size of this level
    level_size: tuple[int, int] = (level_info["width"], level_info["height"])

    layers: list[str] = [
        remove_ext(layer_filename) for layer_filename in level_info["layers"]
    ]
    for layer in layers:
        # Get the background surface for this layer
        with open(level_dir / f"{layer}.png", "rb") as f:
            background_surfaces[layer] = pg.image.load(f)

        # Get the tilemap data for this layer
        tilemap: list[list[bool]] = []
        with open(level_dir / f"{layer}.csv", "r") as f:
            reader = csv.reader(f)
            for raw_row in reader:
                # LDTK's simplified export includes a trailing comma, so drop empty cells
                row: list[str] = [cell for cell in raw_row if cell != ""]
                tilemap.append([bool(int(cell)) for cell in row])

        # Ensure consistent row widths so placement math stays aligned
        unique_widths: set[int] = {len(r) for r in tilemap}
        if len(unique_widths) != 1:
            raise ValueError(
                f"Inconsistent row widths in tilemap for layer {layer}: {unique_widths}"
            )
        tilemaps[layer] = tilemap

        # Get the tile size for this layer
        tile_size = (level_size[0] // len(tilemap[0]), level_size[1] // len(tilemap))
        tile_sizes[layer] = tile_size

    return GameLevel(
        tilemaps, tile_sizes, background_surfaces, level_size, level_info["entities"]
    )
```

## ajishio/src/ajishio/rendering.py
```python
from __future__ import annotations
from collections.abc import Iterable
import colorsys
from pathlib import Path
import pygame as pg
Color = pg.Color
from ajishio.view import view
from ajishio.types import GameSprite


c_aqua = Color(0, 255, 255)
c_black = Color(0, 0, 0)
c_blue = Color(0, 0, 255)
c_dkgray = Color(64, 64, 64)
c_fuchsia = Color(255, 0, 255)
c_gray = Color(128, 128, 128)
c_green = Color(0, 128, 0)
c_lime = Color(0, 255, 0)
c_ltgray = Color(192, 192, 192)
c_maroon = Color(128, 0, 0)
c_navy = Color(0, 0, 128)
c_olive = Color(128, 128, 0)
c_orange = Color(255, 160, 64)
c_purple = Color(128, 0, 128)
c_red = Color(255, 0, 0)
c_silver = Color(192, 192, 192)
c_teal = Color(0, 128, 128)
c_white = Color(255, 255, 255)
c_yellow = Color(255, 255, 0)


def _translate_offset(x: float, y: float) -> tuple[float, float]:
    return (x + view.offset[0], y + view.offset[1])


def make_color_hsv(hue: float, sat: float, val: float) -> Color:
    return Color(*[int(c * 255) for c in colorsys.hsv_to_rgb(hue, sat, val)])


def load_font(font_path: Path | str, size: int) -> pg.font.Font:
    try:
        return pg.font.Font(str(font_path), size)
    except FileNotFoundError:
        return pg.font.Font(None, size)


class Renderer:
    def __init__(self) -> None:
        self._screen: pg.Surface | None = None
        self.set_screen_size(view.window_width, view.window_height)
        self.fit_display()
        self._background_images: Iterable[pg.Surface] = []

        self.draw_color: Color = Color(255, 255, 255)
        self.draw_font: pg.font.Font = pg.font.Font(None, 32)
        self.draw_font_fallbacks: Iterable[pg.font.Font] = []

    def set_screen_size(self, w: float, h: float) -> None:
        self._screen = pg.display.set_mode((w, h))

    def draw_display(self) -> None:
        if self._screen is None:
            return
        scaled_display: pg.Surface = pg.transform.scale(
            self.display, self._screen.get_size()
        )
        _ = self._screen.blit(scaled_display, (0, 0))

    def fit_display(self) -> None:
        self.display = pg.Surface(
            (view.view_wport[view.view_current], view.view_hport[view.view_current]),
            flags=pg.SRCALPHA,
        )

    def fill_background_color(self, color: pg.Color) -> None:
        _ = self.display.fill(color)

    def set_background_images(self, surfaces: Iterable[pg.Surface]) -> None:
        self._background_images = surfaces

    def draw_background_images(self) -> None:
        for bg in self._background_images:
            _ = self.display.blit(bg, view.offset)

    def draw_circle(
        self, x: float, y: float, radius: float, color: pg.Color | None = None
    ) -> None:
        x, y = _translate_offset(x, y)
        _ = pg.draw.circle(
            self.display,
            self.draw_color if color is None else color,
            (x, y),
            radius,
        )

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        outline: bool = False,
        color: pg.Color | None = None,
        alpha: float = 1.0,
    ) -> None:
        x, y = _translate_offset(x, y)
        color = self.draw_color if color is None else color
        color.a = int(alpha * 255)
        rect_surf = pg.Surface((width, height), flags=pg.SRCALPHA)
        if outline:
            _ = pg.draw.rect(rect_surf, color, (0, 0, width, height), 1)
        else:
            _ = rect_surf.fill(color)
        _ = self.display.blit(rect_surf, (x, y))

    def draw_line(
        self, x1: float, y1: float, x2: float, y2: float, color: pg.Color | None = None
    ) -> None:
        x1, y1 = _translate_offset(x1, y1)
        x2, y2 = _translate_offset(x2, y2)
        _ = pg.draw.line(
            self.display,
            self.draw_color if color is None else color,
            (x1, y1),
            (x2, y2),
        )

    def draw_text(
        self, x: float, y: float, string: str, color: pg.Color | None = None
    ) -> None:
        x, y = _translate_offset(x, y)
        surface = self._render_text_with_fallback(
            string, self.draw_color if color is None else color
        )
        _ = self.display.blit(surface, (x, y))

    def text_width(self, string: str) -> int:
        return self._render_text_with_fallback(string, self.draw_color).get_width()

    def text_height(self, string: str) -> int:
        return self._render_text_with_fallback(string, self.draw_color).get_height()

    def draw_sprite(
        self,
        x: float,
        y: float,
        sprite_index: GameSprite,
        image_index: int,
        x_scale: float = 1.0,
        y_scale: float = 1.0,
        rotation: float = 0.0,
        color: pg.Color = c_white,
        alpha: float = 1.0,
    ) -> None:
        if x_scale == 0.0 or y_scale == 0.0:
            return

        scale_x_abs: float = abs(x_scale)
        scale_y_abs: float = abs(y_scale)

        offset_x: float = (
            sprite_index.x_offset
            if x_scale >= 0
            else sprite_index.width - sprite_index.x_offset
        )
        offset_y: float = (
            sprite_index.y_offset
            if y_scale >= 0
            else sprite_index.height - sprite_index.y_offset
        )

        draw_x: float = x - offset_x * scale_x_abs
        draw_y: float = y - offset_y * scale_y_abs
        draw_x, draw_y = _translate_offset(draw_x, draw_y)
        image_index = image_index % len(sprite_index.images)
        image = sprite_index.images[image_index]
        if rotation != 0.0:
            image = pg.transform.rotate(image, rotation)

        if x_scale != 1.0 or y_scale != 1.0:
            image = pg.transform.scale(
                image,
                (
                    int(image.get_width() * scale_x_abs),
                    int(image.get_height() * scale_y_abs),
                ),
            )
            image = pg.transform.flip(image, x_scale < 0, y_scale < 0)
        image.set_alpha(int(alpha * 255))
        if color != c_white:
            _ = image.fill(color, special_flags=pg.BLEND_MULT)
        _ = self.display.blit(image, (draw_x, draw_y))

    def draw_set_font(
        self, font: pg.font.Font, fallbacks: Iterable[pg.font.Font] | None = None
    ) -> None:
        self.draw_font = font
        self.draw_font_fallbacks = [] if fallbacks is None else fallbacks

    def _pick_font_for_char(self, char: str) -> pg.font.Font:
        for font in [self.draw_font, *self.draw_font_fallbacks]:
            glyph_surface = font.render(char, True, self.draw_color)
            tofu_surface = font.render("□", True, self.draw_color)
            if glyph_surface.get_size() == tofu_surface.get_size():
                if pg.image.tobytes(glyph_surface, "RGBA") == pg.image.tobytes(
                    tofu_surface, "RGBA"
                ):
                    continue
            return font
        return self.draw_font

    def _render_text_with_fallback(self, string: str, color: pg.Color) -> pg.Surface:
        if not string:
            return pg.Surface((0, 0), flags=pg.SRCALPHA)

        glyphs: list[tuple[pg.Surface, int]] = []
        cursor_x = 0
        max_h = 0
        for ch in string:
            font = self._pick_font_for_char(ch)
            glyph_surface = font.render(ch, True, color)
            glyphs.append((glyph_surface, cursor_x))
            cursor_x += glyph_surface.get_width()
            if glyph_surface.get_height() > max_h:
                max_h = glyph_surface.get_height()

        rendered = pg.Surface((cursor_x, max_h), flags=pg.SRCALPHA)
        for glyph_surface, gx in glyphs:
            _ = rendered.blit(glyph_surface, (gx, max_h - glyph_surface.get_height()))
        return rendered
```

## ajishio/src/ajishio/sound_loader.py
```python
import pygame as pg
from ajishio.game_sound import GameSound
from pathlib import Path
from ajishio.utils import remove_ext


def load_sounds(sounds_directory: Path) -> dict[str, GameSound]:
    return {
        remove_ext(sound_file.name): load_sound(sound_file)
        for sound_file in sounds_directory.iterdir()
    }


def load_sound(sound_file: Path) -> GameSound:
    sound: pg.mixer.Sound = pg.mixer.Sound(str(sound_file))
    return GameSound(sound)
```

## ajishio/src/ajishio/sprite_loader.py
```python
import json
from ajishio.types import GameSprite
from pathlib import Path
from typing import TypedDict

import pygame as pg


class FrameRect(TypedDict):
    x: int
    y: int
    w: int
    h: int


class FrameData(TypedDict):
    frame: FrameRect


class SpriteInfo(TypedDict):
    frames: dict[str, FrameData]


def load_aseprite_sprites(sprites_directory: Path) -> dict[str, GameSprite]:
    alphabetical_sprite_dirs: list[Path] = sorted(sprites_directory.iterdir())
    return {
        sprite_dir.name: load_aseprite_sprite(sprite_dir)
        for sprite_dir in alphabetical_sprite_dirs
    }


def load_aseprite_sprite(sprite_dir: Path) -> GameSprite:
    images: list[pg.Surface] = []

    png_path: Path = next(sprite_dir.glob("*.png"))

    json_path: Path = next(sprite_dir.glob("*.json"))
    sprite_info: SpriteInfo = json.loads(json_path.read_text())
    frames: dict[str, FrameData] = sprite_info["frames"]

    sprite_width: int = 0
    sprite_height: int = 0

    for data in frames.values():
        dims: FrameRect = data["frame"]
        x, y = dims["x"], dims["y"]
        frame_width, frame_height = dims["w"], dims["h"]
        sprite_width = max(sprite_width, frame_width)
        sprite_height = max(sprite_height, frame_height)
        with open(png_path, "rb") as f:
            images.append(
                pg.image.load(f).subsurface(pg.Rect(x, y, frame_width, frame_height))
            )

    return GameSprite(images, sprite_width, sprite_height)


def sprite_set_offset(sprite: GameSprite, x_offset: float, y_offset: float) -> None:
    sprite.x_offset = x_offset
    sprite.y_offset = y_offset
```

## ajishio/src/ajishio/types.py
```python
from __future__ import annotations
from typing import Protocol, TypedDict, runtime_checkable
from collections.abc import Sequence
from uuid import UUID
from pygame import Surface
from dataclasses import dataclass

type CustomFields = dict[str, object]


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
    customFields: CustomFields


class GameObjectKwargs(TypedDict, total=False):
    sprite_index: GameSprite | None
    collision_mask: CollisionMask | None
    iid: str | None
    width: float
    height: float
    customFields: CustomFields | None


@dataclass
class GameLevel:
    tilemaps: dict[str, list[list[bool]]]
    tile_sizes: dict[str, tuple[int, int]]
    background_surfaces: dict[str, Surface]
    level_size: tuple[int, int]
    entities: dict[str, Sequence[Entity]]


@runtime_checkable
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
    custom_fields: CustomFields

    @property
    def sprite_width(self) -> int: ...

    @property
    def sprite_height(self) -> int: ...

    @classmethod
    def create_from_entity(cls, _entity: Entity) -> IGameObject: ...

    def step(self) -> None: ...

    def draw(self) -> None: ...

    def on_game_end(self) -> None: ...

    def place_meeting(
        self, _x: float, _y: float, _obj: IGameObject | type[IGameObject] | UUID
    ) -> IGameObject | None: ...

    def on_destroy(self) -> None:
        """
        This event is the event to be executed when an instance is destroyed. It is often overlooked
        when adding behaviours to objects, but it can be very useful, for example by creating
        explosion or particle effects when an enemy is killed, or for respawning a new instance of
        the object in another part of the room, or even for adding points to a score.
        """
        ...
```

## ajishio/src/ajishio/utils.py
```python
import inspect
import sys
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar

import pygame as pg
import math

_P = ParamSpec("_P")
_R = TypeVar("_R")


def profile(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    """Decorator that profiles *fn* when ``--profile`` is passed on the command line.

    The ``.prof`` file is saved to the current working directory and named after
    the module that owns the decorated function (e.g. ``platformer.prof``).
    Without ``--profile`` the function runs completely unmodified.

    Example::

        @aj.profile
        def main() -> None:
            aj.game_start()

        main()
    """

    @wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        if "--profile" not in sys.argv:
            return fn(*args, **kwargs)

        import cProfile
        import pstats

        # Derive a friendly name from the owning module's file path.
        module_file = inspect.getfile(fn)
        stem = Path(
            module_file
        ).parent.name  # e.g. "platformer" from .../platformer/main.py
        output_path = Path.cwd() / f"{stem}.prof"

        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return fn(*args, **kwargs)
        finally:
            profiler.disable()
            profiler.dump_stats(output_path)
            _ = pstats.Stats(profiler).sort_stats("cumulative").print_stats(30)
            print(f"\nProfile saved to {output_path.name}")
            print(f"   To visualise: uv run snakeviz {output_path.name}")

    return wrapper


def remove_ext(filename: str) -> str:
    return filename[: filename.rfind(".")]


def room_set_caption(caption: str) -> None:
    pg.display.set_caption(caption)


def lengthdir_x(length: float, direction: float) -> float:
    """
    Returns the length of the x component of a vector with the given length and direction (in radians).
    """
    return length * math.cos(direction)


def lengthdir_y(length: float, direction: float) -> float:
    """
    Returns the length of the y component of a vector with the given length and direction (in radians).
    """
    return length * math.sin(direction)


def clamp(value: float, min: float, max: float) -> float:
    return min if value < min else max if value > max else value


def map_value(
    value: float, min: float, max: float, new_min: float, new_max: float
) -> float:
    return (value - min) / (max - min) * (new_max - new_min) + new_min


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def point_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)
```

## ajishio/src/ajishio/view.py
```python
from __future__ import annotations


class View:
    _instance: View | None = None

    def __new__(cls) -> View:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self) -> None:
        self.view_current: int = 0
        self.window_width: int = 800
        self.window_height: int = 600
        self.view_xport: dict[int, float] = {self.view_current: 0}
        self.view_yport: dict[int, float] = {self.view_current: 0}
        self.view_wport: dict[int, float] = {self.view_current: self.window_width}
        self.view_hport: dict[int, float] = {self.view_current: self.window_height}

    def view_set_wport(self, view: int, w: float) -> None:
        self.view_wport[view] = w

    def view_set_hport(self, view: int, h: float) -> None:
        self.view_hport[view] = h

    def view_set_xport(self, view: int, x: float) -> None:
        self.view_xport[view] = x

    def view_set_yport(self, view: int, y: float) -> None:
        self.view_yport[view] = y

    def window_set_size(self, w: int, h: int) -> None:
        self.window_width = w
        self.window_height = h
        # Keep the default viewport in sync with the window size
        self.view_wport[self.view_current] = w
        self.view_hport[self.view_current] = h

    @property
    def offset(self) -> tuple[float, float]:
        return (
            -self.view_xport[self.view_current],
            -self.view_yport[self.view_current],
        )


view = View()
```
