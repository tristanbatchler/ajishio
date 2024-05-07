from __future__ import annotations
from uuid import UUID
from ajishio.input import _input, QuitInterrupt
from ajishio.view import _view
from ajishio.rendering import _renderer
from ajishio.level_loader import GameLevel
import pygame as pg
import sys

# Import GameObject class only for type hinting, must avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ajishio.game_object import GameObject

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

    def set_rooms(self, rooms: list[GameLevel]) -> None:
        self._rooms = rooms

    def register_objects(self, *objects: type[GameObject]) -> None:
        for obj in objects:
            globals()[obj.__name__] = obj

    def room_goto(self, index) -> None:
        for instance in self._game_objects.copy().values():
            self.instance_destroy(instance)

        level: GameLevel = self._rooms[index]

        self.room_set_size(*level.level_size)
        _view.view_set_wport(_view.view_current, self.room_width)
        _view.view_set_hport(_view.view_current, self.room_height)

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
                        tile_cls(x * tile_size[0], y * tile_size[1], *tile_size)
                        

        # Load the entities
        for entity_type, entities in level.entities.items():
            for entity in entities:
                try:
                    entity_cls: type = globals()[entity_type]
                except KeyError:
                    raise ValueError(f"{entity_type} object not found in engine namespace. Make sure you have registered it with `aj.register_objects({entity_type})")
                entity_cls(**entity)
                
                

        self.room = index

    def room_goto_next(self) -> None:
        self.room_goto(self.room + 1)

    def room_goto_previous(self) -> None:
        self.room_goto(self.room - 1)

    def room_restart(self) -> None:
        self.room_goto(self.room)

    def game_set_speed(self, speed: float) -> None:       
        self.room_speed = speed
        self.delta_time = 1 / self.room_speed
            
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

    def add_object(self, obj: GameObject) -> None:
        self._game_objects[obj.id] = obj

    def instance_destroy(self, obj: GameObject) -> None:
        self._game_objects.pop(obj.id)

    def instance_exists(self, obj: type[GameObject]) -> bool:
        return self.instance_find(obj) is not None
    
    def instance_find(self, obj: type[GameObject], n: int = 0) -> GameObject | None:
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

            self.delta_time = self._clock.tick()

            try:
                _input.poll()
            except QuitInterrupt:
                self._game_running = False

            game_objects_copy = self._game_objects.copy()

            for obj in game_objects_copy.values():
                obj.handle_input()

            if self.room_speed == 0:
                continue
            self._last_render_time += self.delta_time
            room_speed_ms: float = 1000 // self.room_speed
            if self._last_render_time >= room_speed_ms:
                self._last_render_time %= room_speed_ms
                _renderer.fit_display()
                _renderer.fill_background_color(self.room_background_color)
                _renderer.draw_background_images()
            
                for obj in game_objects_copy.values():
                    obj.step()
                    obj.draw()

                _renderer.draw_display()
                pg.display.update()
        
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
        
# These do not need to be evaluated at runtime, since they are references to methods, so they go here
game_set_speed = _engine.game_set_speed
room_set_width = _engine.room_set_width
room_set_height = _engine.room_set_height
room_set_background = _engine.room_set_background
game_start = _engine.game_start
instance_destroy = _engine.instance_destroy
instance_exists = _engine.instance_exists
instance_find = _engine.instance_find
set_rooms = _engine.set_rooms
register_objects = _engine.register_objects
room_goto = _engine.room_goto
room_goto_next = _engine.room_goto_next
room_goto_previous = _engine.room_goto_previous
room_restart = _engine.room_restart