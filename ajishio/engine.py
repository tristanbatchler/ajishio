from __future__ import annotations

from collections.abc import Iterable, Callable
from logging import Logger
from typing import TYPE_CHECKING, cast
from uuid import UUID
from ajishio.input import input
from ajishio.view import view
from ajishio.types import GameLevel, IGameObject
from ajishio.rendering import Renderer
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

        self.room_set_size(
            view.view_wport[view.view_current], view.view_hport[view.view_current]
        )
        self.game_set_speed(60)
        self.room_set_background(pg.Color(0, 0, 0))

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
                        entity_type, entity_type,
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
                    self._last_render_time %= self.room_speed
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
                    audio for audio in self._audio_playing
                    if not audio.is_finished(self.delta_time)
                ]

            except KeyboardInterrupt:
                self._game_running = False

        pg.quit()
        sys.exit()

    def get_game_objects(self) -> Iterable[IGameObject]:
        return self._game_objects.values()

    def get_game_object_by_id(self, id: UUID) -> IGameObject | None:
        return self._game_objects.get(id)

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

