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
    return any(event.type == pg.MOUSEBUTTONDOWN and event.button == mb for event in input.events)


def keyboard_check(key: int) -> bool:
    return pg.key.get_pressed()[key]


def mouse_check_button(mb: int) -> bool:
    return pg.mouse.get_pressed()[mb]


def ord(char: str) -> int:
    return pg.key.key_code(char)


vk_left: int = pg.K_LEFT
vk_right: int = pg.K_RIGHT
vk_up: int = pg.K_UP
vk_down: int = pg.K_DOWN
vk_space: int = pg.K_SPACE
vk_escape: int = pg.K_ESCAPE
vk_enter: int = pg.K_RETURN
mb_left: int = 0
mb_middle: int = 1
mb_right: int = 2
