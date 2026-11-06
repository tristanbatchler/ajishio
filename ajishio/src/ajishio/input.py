from __future__ import annotations
from dataclasses import dataclass, field
from typing import cast
import pygame as pg


class QuitInterrupt(Exception):
    pass


@dataclass
class _KeyRepeat:
    next_fire_ms: int = 0
    last_checked_ms: int = 0


@dataclass
class _RepeatState:
    keys: dict[int, _KeyRepeat] = field(default_factory=dict)


_REPEAT_FORGET_MS = 250


class Input:
    def __init__(self) -> None:
        self.prev_events: list[pg.event.Event] | None = None
        self.events: list[pg.event.Event] = []
        self.repeat: _RepeatState = _RepeatState()


input = Input()


def keyboard_check_pressed(key: int) -> bool:
    pressed_now: bool = any(
        event.type == pg.KEYDOWN and cast(int, event.key) == key
        for event in input.events
    )
    if input.prev_events is None:
        return pressed_now
    pressed_before: bool = any(
        event.type == pg.KEYDOWN and cast(int, event.key) == key
        for event in input.prev_events
    )
    return pressed_now and not pressed_before


def keyboard_check_repeat(
    key: int, delay: float = 0.35, interval: float = 0.05
) -> bool:
    """
    True when a key goes down and then, while it's held, again every `interval` seconds once
    `delay` seconds have passed: how text fields, lists and menus want their keys.
    """
    now = pg.time.get_ticks()
    if not pg.key.get_pressed()[key]:
        _ = input.repeat.keys.pop(key, None)
        # A tap shorter than a frame is down and up again before anyone looks.
        return any(
            event.type == pg.KEYDOWN and cast(int, event.key) == key
            for event in input.events
        )
    state = input.repeat.keys.get(key)
    # (nobody asked for a while: it may have been let go meanwhile, so this is a new press)
    if state is None or now - state.last_checked_ms > _REPEAT_FORGET_MS:
        input.repeat.keys[key] = _KeyRepeat(now + int(delay * 1000), now)
        return True
    state.last_checked_ms = now
    if now >= state.next_fire_ms:
        state.next_fire_ms = now + int(interval * 1000)
        return True
    return False


def keyboard_string() -> str:
    """The text typed since the last frame, with the keyboard's layout and shift applied."""
    return "".join(
        cast(str, event.text) for event in input.events if event.type == pg.TEXTINPUT
    )


def input_activity() -> bool:
    """Whether the player pressed, clicked or moved anything this frame: for idle timers."""
    return any(
        event.type
        in (pg.KEYDOWN, pg.MOUSEBUTTONDOWN, pg.MOUSEMOTION, pg.MOUSEWHEEL)
        for event in input.events
    )


def mouse_check_button_pressed(mb: int) -> bool:
    pressed_now: bool = any(
        event.type == pg.MOUSEBUTTONDOWN and cast(int, event.button) == mb
        for event in input.events
    )
    if input.prev_events is None:
        return pressed_now
    pressed_before: bool = any(
        event.type == pg.MOUSEBUTTONDOWN and cast(int, event.button) == mb
        for event in input.prev_events
    )
    return pressed_now and not pressed_before


def keyboard_check_released(key: int) -> bool:
    return any(
        event.type == pg.KEYUP and cast(int, event.key) == key for event in input.events
    )


def mouse_check_button_released(mb: int) -> bool:
    return any(
        event.type == pg.MOUSEBUTTONUP and cast(int, event.button) == mb
        for event in input.events
    )


def keyboard_check(key: int) -> bool:
    return pg.key.get_pressed()[key]


def mouse_check_button(mb: int) -> bool:
    pressed = pg.mouse.get_pressed()

    if mb in (mb_left, mb_middle, mb_right):
        return pressed[mb - 1]

    return False


def mouse_wheel_up() -> bool:
    return any(
        event.type == pg.MOUSEWHEEL and cast(int, event.y) > 0 for event in input.events
    )


def mouse_wheel_down() -> bool:
    return any(
        event.type == pg.MOUSEWHEEL and cast(int, event.y) < 0 for event in input.events
    )


def ord(char: str) -> int:
    return pg.key.key_code(char)


vk_left: int = pg.K_LEFT
vk_right: int = pg.K_RIGHT
vk_up: int = pg.K_UP
vk_down: int = pg.K_DOWN
vk_space: int = pg.K_SPACE
vk_escape: int = pg.K_ESCAPE
vk_enter: int = pg.K_RETURN
vk_backspace: int = pg.K_BACKSPACE
vk_tab: int = pg.K_TAB
vk_delete: int = pg.K_DELETE
vk_home: int = pg.K_HOME
vk_end: int = pg.K_END
vk_pageup: int = pg.K_PAGEUP
vk_pagedown: int = pg.K_PAGEDOWN
vk_shift: int = pg.K_LSHIFT
vk_control: int = pg.K_LCTRL

mb_left: int = 1
mb_middle: int = 2
mb_right: int = 3
