from __future__ import annotations
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
        self.prev_events: list[pg.event.Event] | None = None
        self.events: list[pg.event.Event] = []


_input: Input = Input()


def keyboard_check_pressed(key: int) -> bool:
    pressed_now: bool = any(
        event.type == pg.KEYDOWN and event.key == key for event in _input.events
    )
    if _input.prev_events is None:
        return pressed_now
    pressed_before: bool = any(
        event.type == pg.KEYDOWN and event.key == key for event in _input.prev_events
    )
    return pressed_now and not pressed_before


def keyboard_check_released(key: int) -> bool:
    return any(event.type == pg.KEYUP and event.key == key for event in _input.events)


def keyboard_check(key: int) -> bool:
    return pg.key.get_pressed()[key]


def ord(char: str) -> int:
    return pg.key.key_code(char)


vk_left: int = pg.K_LEFT
vk_right: int = pg.K_RIGHT
vk_up: int = pg.K_UP
vk_down: int = pg.K_DOWN
vk_space: int = pg.K_SPACE
