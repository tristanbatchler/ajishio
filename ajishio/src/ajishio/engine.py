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
import ajishio.pyqtree as pyqtree
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
        self._spatial_index: pyqtree.Index | None = None

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

    def _get_obj_aabb(self, obj: IGameObject) -> tuple[float, float, float, float] | None:
        """Return (left, top, right, bottom) world AABB for obj, or None if no collision mask."""
        msk = obj.collision_mask
        if msk is None:
            return None
        return (
            obj.x + msk.bbleft,
            obj.y + msk.bbtop,
            obj.x + msk.bbright,
            obj.y + msk.bbbottom,
        )

    def _rebuild_spatial_index(self) -> None:
        margin = 2_000.0
        bounds = (-margin, -margin, self.room_width + margin, self.room_height + margin)
        self._spatial_index = pyqtree.Index(bbox=bounds)

        def is_inside(rect: tuple[float, float, float, float]) -> bool:
            lf, tp, rt, bm = rect
            bl, bt, br, bb = bounds
            return lf >= bl and rt <= br and tp >= bt and bm <= bb

        for obj in self._game_objects.values():
            if obj in self._game_objects_to_destroy:
                continue
            aabb = self._get_obj_aabb(obj)
            if aabb is not None and is_inside(aabb):
                self._spatial_index.insert(obj, aabb)  # pyright: ignore[reportUnknownMemberType]

        for obj in self._game_objects_to_add:
            aabb = self._get_obj_aabb(obj)
            if aabb is not None and is_inside(aabb):
                self._spatial_index.insert(obj, aabb)  # pyright: ignore[reportUnknownMemberType]

    def collision_rectangle_list(
        self, left: float, top: float, right: float, bottom: float
    ) -> list[IGameObject]:
        """
        This function checks a rectangular area for a collision with all instances. It returns the
        list of all instances in the supplied rectangular region.

        This function is the same as the collision_rectangle() function, only instead of just
        detecting one instance at a time, it will detect multiple instances. You supply the x/y
        positions of the top left and bottom right of the area to check.
        """
        if self._spatial_index is None:
            return []
        # RectQuadTreeObjects.query returns a list of objects directly
        return cast(list[IGameObject], self._spatial_index.intersect((left, top, right, bottom)))  # pyright: ignore[reportUnknownMemberType]

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
            # Create a tiny rectangle around the point
            query_rect = (x - epsilon, y - epsilon, x + epsilon, y + epsilon)
            candidates = self.collision_rectangle_list(*query_rect)
            for g_o in candidates:
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
        left, right = (x1, x2) if x1 < x2 else (x2, x1)
        top, bottom = (y1, y2) if y1 < y2 else (y2, y1)

        if isinstance(obj, type):
            candidates = self.collision_rectangle_list(left, top, right, bottom)
            for g_o in candidates:
                if not_these is not None and g_o in not_these:
                    continue
                if isinstance(g_o, obj):
                    # precise check (reuse the concrete instance branch)
                    if self.collision_rectangle(left, top, right, bottom, g_o, not_these):
                        return g_o
            return None

        if isinstance(obj, UUID):
            game_obj = self.get_game_object_by_id(obj)
            if game_obj is None:
                return None
            return self.collision_rectangle(left, top, right, bottom, game_obj, not_these)

        if not_these is not None and obj in not_these:
            return None

        o = obj
        o_msk: CollisionMask | None = o.collision_mask

        if o_msk is None:
            return None

        if (
            left < obj.x + o_msk.bbright
            and right > obj.x + o_msk.bbleft
            and top < obj.y + o_msk.bbbottom
            and bottom > obj.y + o_msk.bbtop
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

                    self._rebuild_spatial_index()

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

                    self._rebuild_spatial_index()

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
