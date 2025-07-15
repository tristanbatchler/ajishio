from __future__ import annotations
from uuid import UUID
from ajishio.input import _input, QuitInterrupt
from ajishio.view import _view
from ajishio.rendering import _renderer
from ajishio.level_loader import GameLevel
import pygame as pg
import sys
import logging

# Import classes only for type hinting, must avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ajishio.game_object import GameObject
    from ajishio.sound_loader import GameSound

epsilon: float = 0.00001

class Engine:
    _instance: Engine | None = None

    def __new__(cls) -> Engine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.room_width: float
        self.room_height: float
        self.room_speed: float
        self.room_background_color: pg.Color
        self.room: int = 0
        self.delta_time: float
        
        self.room_set_size(_view.view_wport[_view.view_current], _view.view_hport[_view.view_current])
        self.game_set_speed(60)
        self.room_set_background(pg.Color(0, 0, 0))

        self._clock: pg.time.Clock = pg.time.Clock()
        self._last_render_time: float = 0
        self._game_objects: dict[UUID, GameObject] = {}
        self._game_running: bool

        self._rooms: list[GameLevel] = []
        self._audio_playing: list[GameSound] = []

        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

    def set_rooms(self, rooms: list[GameLevel]) -> None:
        self._rooms = rooms

    def register_objects(self, *objects: type[GameObject]) -> None:
        for obj in objects:
            globals()[obj.__name__] = obj

    def room_goto(self, index) -> None:
        # Remove just the non-persistent instances
        for instance in self._game_objects.copy().values():
            if not instance.persistent:
                self.instance_destroy(instance)

        level: GameLevel = self._rooms[index]

        self.room_set_size(*level.level_size)

        # Draw the level
        _renderer.set_background_images(list(level.background_surfaces.values()))

        # Load the tilemaps
        for layer, tilemap in level.tilemaps.items():
            tile_size: tuple[int, int] = level.tile_sizes[layer]

            for y, row in enumerate(tilemap):
                for x, cell in enumerate(row):
                    if cell:
                        try:
                            tile_cls: type = globals()[layer]
                        except KeyError:
                            raise ValueError(f"{layer} object not found in engine namespace. Make sure you have registered it with `aj.register_objects({layer})")
                        tile_cls(x * tile_size[0], y * tile_size[1], width=tile_size[0], height=tile_size[1])
                        

        # Load the entities
        for entity_type, entities in level.entities.items():
            for entity in entities:
                try:
                    entity_cls: type[GameObject] = globals()[entity_type]
                except KeyError:
                    self._logger.warning(f"{entity_type} object not found in engine namespace. Make sure you have registered it with `aj.register_objects({entity_type})")
                    continue

                if not (self.instance_exists(entity_cls) and entity_cls.persistent):
                    entity_cls(**entity)

        self.room = index

    def room_goto_next(self) -> None:
        self.room_goto(self.room + 1)

    def room_goto_previous(self) -> None:
        self.room_goto(self.room - 1)

    def room_restart(self) -> None:
        self.room_goto(self.room)

    def game_restart(self) -> None:
        for obj in self._game_objects.copy().values():
            self.instance_destroy(obj)
        self.room_goto(0)

    def game_end(self) -> None:
        self._game_running = False
        for obj in self._game_objects.copy().values():
            obj.on_game_end()

    def game_set_speed(self, speed: float) -> None:       
        self.room_speed = speed
        if speed != 0:
            self.delta_time = 1 / self.room_speed # seconds
            
    def room_set_size(self, w: float, h: float) -> None:
        self.room_width = w
        self.room_height = h
        _renderer.set_screen_size(_view.window_width, _view.window_height)
        _renderer.fit_display()

    def room_set_width(self, w: int) -> None:
        self.room_set_size(w, self.room_height)

    def room_set_height(self, h: int) -> None:
        self.room_set_size(self.room_width, h)

    def room_set_background(self, color: pg.Color) -> None:
        self.room_background_color = color

    def audio_play_sound(self, index: GameSound, loop: bool = False, gain: float = 1) -> None:
        self._audio_playing.append(index)
        index._play(loop=loop, gain=gain)

    def audio_is_playing(self, index: GameSound) -> bool:
        return index in self._audio_playing

    def add_object(self, obj: GameObject) -> None:
        self._game_objects[obj.id] = obj

    def instance_destroy(self, obj: GameObject) -> None:
        try:
            self._game_objects.pop(obj.id)
        except KeyError:
            pass

    def instance_count(self, obj: type[GameObject]) -> int:
        count: int = 0
        for g_o in self._game_objects.values():
            if issubclass(type(g_o), obj):
                count += 1
        return count

    def instance_exists(self, obj: type[GameObject]) -> bool:
        return self.instance_count(obj) > 0

    def instance_find(self, obj: type[GameObject] | str, n: int = 0) -> GameObject | None:
        # If obj is a IID, find the object with that IID (it is unique)
        if isinstance(obj, str):
            for g_o in self._game_objects.values():
                if g_o.iid == obj:
                    return g_o
            return None

        # If obj is a type, find the nth object of that type
        count: int = 0
        for g_o in self._game_objects.values():
            if issubclass(type(g_o), obj):
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
                _input.events += pg.event.get()

                if any(event.type == pg.QUIT for event in _input.events):
                    self.game_end()

                self.delta_time = self._clock.tick(self.room_speed) / 1000 # milliseconds to seconds

                if self.room_speed == 0:
                    continue
                self._last_render_time += self.delta_time
                if self._last_render_time >= 1 / self.room_speed:
                    self._last_render_time %= self.room_speed
                    _renderer.fit_display()
                    _renderer.fill_background_color(self.room_background_color)
                    _renderer.draw_background_images()
                    
                    for obj in self._game_objects.copy().values():
                        obj.step()
                        obj.draw()

                    # Only clear the input after all objects have had a chance to process it
                    _input.prev_events = _input.events.copy()
                    _input.events.clear()

                    _renderer.draw_display()
                    pg.display.update()
                    

                for audio in self._audio_playing:
                    if audio._is_finished():
                        self._audio_playing.remove(audio)
                        
            except KeyboardInterrupt:
                self._game_running = False

        pg.quit()
        sys.exit()

_engine: Engine = Engine()

# Put exposed instance variables here to help with code completion, but they are actually evaluated 
# at runtime by the __getattr__ method in ajishio.__init__.py
room_speed: float
room_width: int
room_height: int
room_background_color: pg.Color
room: int
delta_time: float
        
# These do not need to be evaluated at runtime, since they are references to methods, so they go here
game_set_speed = _engine.game_set_speed
room_set_width = _engine.room_set_width
room_set_height = _engine.room_set_height
room_set_background = _engine.room_set_background
game_start = _engine.game_start
instance_destroy = _engine.instance_destroy
instance_count = _engine.instance_count
instance_exists = _engine.instance_exists
instance_find = _engine.instance_find
set_rooms = _engine.set_rooms
register_objects = _engine.register_objects
room_goto = _engine.room_goto
room_goto_next = _engine.room_goto_next
room_goto_previous = _engine.room_goto_previous
room_restart = _engine.room_restart
game_restart = _engine.game_restart
game_end = _engine.game_end
audio_play_sound = _engine.audio_play_sound
audio_is_playing = _engine.audio_is_playing
