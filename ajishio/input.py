from __future__ import annotations
from typing import Callable
import pygame as pg

class QuitInterrupt(Exception):
    pass

class Input:
    _instance: Input | None = None

    def __new__(cls, *args, **kwargs) -> Input:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self) -> None:
        self._keys_pressed: set[int] = set()
        self._keys_held: set[int] = set()
        self._keys_released: set[int] = set()

    def poll(self) -> None:
        self._keys_pressed = set()
        self._keys_released = set()

        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    raise QuitInterrupt
                case pg.KEYDOWN:
                    self._keys_pressed.add(event.key)
                    self._keys_held.add(event.key)
                case pg.KEYUP:
                    self._keys_held.discard(event.key)
                    self._keys_released.add(event.key)
                case _:
                    pass
    
    def keyboard_check_pressed(self, key: int) -> bool:
        return key in self._keys_pressed
    
    def keyboard_check(self, key: int) -> bool:
        return key in self._keys_held
    
    def keyboard_check_released(self, key: int) -> bool:
        return key in self._keys_released

_input: Input = Input()
keyboard_check_pressed: Callable[[int], bool] = _input.keyboard_check_pressed
keyboard_check: Callable[[int], bool] = _input.keyboard_check
keyboard_check_released: Callable[[int], bool] = _input.keyboard_check_released


vk_left: int = pg.K_LEFT
vk_right: int = pg.K_RIGHT
vk_up: int = pg.K_UP
vk_down: int = pg.K_DOWN
vk_space: int = pg.K_SPACE