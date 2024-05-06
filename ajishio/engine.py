from __future__ import annotations
from uuid import uuid4, UUID
from ajishio.input import _input, QuitInterrupt
from ajishio.view import _view
from dataclasses import dataclass
from enum import Enum
import pygame as pg
import math
import sys
from typing import BinaryIO

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
        self._screen: pg.Surface
        self._display: pg.Surface
        self._background_image: pg.Surface | None = None

        pg.init()
        self.room_set_size(_view.view_wport[_view.view_current], _view.view_hport[_view.view_current])
        self.game_set_speed(60, GameSpeedConstant.FPS)
        self.room_set_background(pg.Color(0, 0, 0))
        room_set_caption("")

        self._clock: pg.time.Clock = pg.time.Clock()
        self._last_render_time: float = 0
        self._game_objects: dict[UUID, GameObject] = {}
        self._game_running: bool

    def game_set_speed(self, speed: float, type: GameSpeedConstant) -> None:       
        match type:
            case GameSpeedConstant.FPS:
                self.room_speed = speed
            case GameSpeedConstant.MICROSECONDS:
                self.room_speed = 1000000 / speed
            case _:
                raise ValueError("Invalid GameSpeedConstant")
            
    def room_set_size(self, w: float, h: float) -> None:
        self.room_width = w
        self.room_height = h
        self._screen = pg.display.set_mode((self.room_width, self.room_height))
        self._fit_display()

    def _fit_display(self) -> None:
        self._display = pg.Surface((_view.view_wport[_view.view_current], _view.view_hport[_view.view_current]))

    def _get_display(self) -> pg.Surface:
        return self._display

    def room_set_width(self, w: int) -> None:
        self.room_set_size(w, self.room_height)

    def room_set_height(self, h: int) -> None:
        self.room_set_size(self.room_width, h)

    def room_set_background_image(self, surface: pg.Surface) -> None:
        self._background_image = surface

    def room_set_background(self, color: pg.Color) -> None:
        self.room_background_color = color

    def add_object(self, obj: GameObject) -> None:
        self._game_objects[obj.id] = obj

    def instance_destroy(self, obj: GameObject) -> None:
        self._game_objects.pop(obj.id)

    def game_start(self) -> None:
        self._game_running = True
        while self._game_running:
            delta_time = self._clock.tick()

            try:
                _input.poll()
            except QuitInterrupt:
                self._game_running = False

            game_objects_copy = self._game_objects.copy()

            for obj in game_objects_copy.values():
                obj.handle_input()

            if self.room_speed == 0:
                continue
            self._last_render_time += delta_time
            room_speed_ms: float = 1000 // self.room_speed
            if self._last_render_time >= room_speed_ms:
                self._last_render_time %= room_speed_ms

                self._fit_display()

                self._display.fill(self.room_background_color)
                if self._background_image is not None:
                    self._display.blit(self._background_image, _view.offset)
            
                for obj in game_objects_copy.values():
                    obj.step()
                    obj.draw()

                scaled_display: pg.Surface = pg.transform.scale(self._display, self._screen.get_size())
                self._screen.blit(scaled_display, (0, 0))


                pg.display.update()
        
        pg.quit()
        sys.exit()

def room_set_caption(caption: str) -> None:
    pg.display.set_caption(caption)

def lengthdir_x(length: float, direction: float) -> float:
    return length * math.cos(direction)

def lengthdir_y(length: float, direction: float) -> float:
    return length * math.sin(direction)

def clamp(value: float, min: float, max: float) -> float:
    return min if value < min else max if value > max else value

def map_value(value: float, min: float, max: float, new_min: float, new_max: float) -> float:
    return (value - min) / (max - min) * (new_max - new_min) + new_min

def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


class GameSpeedConstant(Enum):
    FPS = 0
    MICROSECONDS = 1

class BBoxMode(Enum):
    AUTOMATIC = 0
    FULL_IMAGE = 1
    USER_DEFINED = 2

class BBoxKind(Enum):
    RECTANGULAR = 0
    ELLIPSE = 1
    DIAMOND = 2
    PRECISE = 3

@dataclass
class CollisionMask:
    bboxmode: BBoxMode = BBoxMode.AUTOMATIC
    sepmasks: bool = True
    bbleft: float = 0
    bbtop: float = 0
    bbright: float = 0
    bbbottom: float = 0
    kind: BBoxKind = BBoxKind.RECTANGULAR 
    tolerance: int = 0


class GameObject:
    def __init__(self, x: float = 0, y: float = 0, collision_mask: CollisionMask | None = None) -> None:
        self.x: float = x
        self.y: float = y
        self.collision_mask: CollisionMask | None = collision_mask
        self.id: UUID = uuid4()
        _engine.add_object(self)

    def step(self) -> None:
        pass

    def draw(self) -> None:
        pass

    def handle_input(self) -> None:
        pass

    def place_meeting(self, x: float, y: float, obj: GameObject | type[GameObject] | UUID) -> GameObject | None:
        if isinstance(obj, GameObject):
            o: GameObject = obj
            s_msk: CollisionMask | None = self.collision_mask
            o_msk: CollisionMask | None = o.collision_mask
            
            if s_msk is None or o_msk is None:
                return None

            match s_msk.kind:
                case BBoxKind.RECTANGULAR:
                    return o if check_rectangular_collision(x, y, s_msk, o.x, o.y, o_msk) else None
                case _:
                    raise NotImplementedError("Collision between non-rectangular masks not implemented")

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
    
def check_rectangular_collision(x1: float, y1: float, mask1: CollisionMask, x2: float, y2: float, mask2: CollisionMask) -> bool:
    assert mask1.kind == BBoxKind.RECTANGULAR

    match mask2.kind:
        case BBoxKind.RECTANGULAR:
            return (x1 + mask1.bbleft < x2 + mask2.bbright and
                    x1 + mask1.bbright > x2 + mask2.bbleft and
                    y1 + mask1.bbtop < y2 + mask2.bbbottom and
                    y1 + mask1.bbbottom > y2 + mask2.bbtop)
        case _:
            raise NotImplementedError("Collision between rectangular and other mask types not implemented")

_engine: Engine = Engine()

# Put exposed instance variables here to help with code completion, but they are actually evaluated 
# at runtime by the __getattr__ method in ajishio.__init__.py
room_speed: float
room_width: int
room_height: int
room_background_color: pg.Color
        
# These do not need to be evaluated at runtime, since they are references to methods, so they go here
game_set_speed = _engine.game_set_speed
room_set_width = _engine.room_set_width
room_set_height = _engine.room_set_height
room_set_background = _engine.room_set_background
room_set_background_image = _engine.room_set_background_image
game_start = _engine.game_start
instance_destroy = _engine.instance_destroy