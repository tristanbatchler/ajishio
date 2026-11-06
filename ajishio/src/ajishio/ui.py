"""
A small immediate-mode GUI: call these from `draw_gui`, every frame, for whatever is on screen.
There's no state to keep in sync. A button is a call that draws one and returns whether it was
clicked, so what's shown is simply what the code asked for this frame.

Panels stack in the order they're drawn. A widget only takes the mouse when no panel drawn after
its own covers it, and `gui_mouse_over()` tells the game not to act on a click meant for the GUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame as pg

import ajishio._context as _ctx
from ajishio.input import (
    keyboard_check_repeat,
    keyboard_string,
    mb_left,
    mouse_check_button_pressed,
    mouse_wheel_down,
    mouse_wheel_up,
    vk_backspace,
    vk_delete,
    vk_end,
    vk_home,
    vk_left,
    vk_right,
)
from ajishio.rendering import Color

Rect = tuple[float, float, float, float]


@dataclass
class GuiTheme:
    """What the widgets look like. Change the fields of `aj.gui_theme` to restyle them all."""

    panel: Color = field(default_factory=lambda: Color(20, 20, 30))
    panel_alpha: float = 0.92
    border: Color = field(default_factory=lambda: Color(92, 88, 120))
    title: Color = field(default_factory=lambda: Color(200, 170, 255))
    text: Color = field(default_factory=lambda: Color(225, 225, 230))
    text_dim: Color = field(default_factory=lambda: Color(140, 140, 155))
    button: Color = field(default_factory=lambda: Color(48, 46, 68))
    button_hover: Color = field(default_factory=lambda: Color(78, 72, 112))
    button_disabled: Color = field(default_factory=lambda: Color(32, 32, 40))
    bar_back: Color = field(default_factory=lambda: Color(40, 40, 50))
    field_back: Color = field(default_factory=lambda: Color(12, 12, 18))
    field_focus: Color = field(default_factory=lambda: Color(168, 100, 205))
    padding: int = 8


gui_theme = GuiTheme()


@dataclass
class _UiState:
    # Panels drawn last frame, in order: what covers what is only known once they've all been
    # drawn, so a widget checks against the frame before.
    previous_panels: list[Rect] = field(default_factory=list)
    panels: list[Rect] = field(default_factory=list)
    click_taken: bool = False
    scroll_offsets: dict[str, float] = field(default_factory=dict)
    scroll_stack: list[tuple[str, Rect, float]] = field(default_factory=list)
    cursors: dict[str, int] = field(default_factory=dict)


_state = _UiState()


def end_frame() -> None:
    """Called by the engine after the GUI pass."""
    _state.previous_panels = _state.panels
    _state.panels = []
    _state.click_taken = False
    _state.scroll_stack.clear()


def _mouse() -> tuple[int, int]:
    return pg.mouse.get_pos()


def gui_mouse_in_rect(x: float, y: float, w: float, h: float) -> bool:
    mx, my = _mouse()
    return x <= mx < x + w and y <= my < y + h


def gui_mouse_over() -> bool:
    """Whether the mouse is over a panel: the game shouldn't act on a click there."""
    mx, my = _mouse()
    return any(
        x <= mx < x + w and y <= my < y + h for x, y, w, h in _state.previous_panels
    )


def _widget_has_mouse(x: float, y: float, w: float, h: float) -> bool:
    if not gui_mouse_in_rect(x, y, w, h):
        return False
    if _state.scroll_stack:
        _, (sx, sy, sw, sh), _ = _state.scroll_stack[-1]
        if not gui_mouse_in_rect(sx, sy, sw, sh):
            return False
    # Covered by a panel drawn after the one this widget is in?
    mx, my = _mouse()
    for px, py, pw, ph in _state.previous_panels[len(_state.panels) :]:
        if px <= mx < px + pw and py <= my < py + ph:
            return False
    return True


def _take_click() -> bool:
    if _state.click_taken or not mouse_check_button_pressed(mb_left):
        return False
    _state.click_taken = True
    return True


def gui_panel(x: float, y: float, w: float, h: float, title: str = "") -> None:
    """Draw a window background. Everything drawn after it, until the next panel, is on it."""
    t = gui_theme
    engine = _ctx.engine
    _state.panels.append((x, y, w, h))
    engine.draw_rectangle(x, y, x + w, y + h, color=t.panel, alpha=t.panel_alpha)
    engine.draw_rectangle(x, y, x + w, y + h, outline=True, color=t.border)
    if title:
        engine.draw_text(x + t.padding, y + t.padding // 2, title, t.title)


def gui_label(
    x: float,
    y: float,
    text: str,
    color: Color | None = None,
    max_width: float | None = None,
) -> None:
    """Draw one line of text, cut short with ".." if it won't fit `max_width`."""
    engine = _ctx.engine
    if max_width is not None and engine.text_width(text) > max_width:
        while text and engine.text_width(text + "..") > max_width:
            text = text[:-1]
        text += ".."
    engine.draw_text(x, y, text, gui_theme.text if color is None else color)


def gui_label_wrapped(
    x: float,
    y: float,
    text: str,
    max_width: float,
    color: Color | None = None,
    line_height: float | None = None,
) -> float:
    """Draw wrapped text and return the height it took."""
    engine = _ctx.engine
    lines = engine.text_wrap(text, max_width)
    step = engine.text_height("Ag") if line_height is None else line_height
    for i, line in enumerate(lines):
        if line:
            engine.draw_text(
                x, y + i * step, line, gui_theme.text if color is None else color
            )
    return len(lines) * step


def gui_button(
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    enabled: bool = True,
    color: Color | None = None,
) -> bool:
    """Draw a button. True on the frame it's clicked."""
    t = gui_theme
    engine = _ctx.engine
    hover = enabled and _widget_has_mouse(x, y, w, h)
    back = t.button_disabled if not enabled else t.button_hover if hover else t.button
    engine.draw_rectangle(x, y, x + w, y + h, color=back)
    engine.draw_rectangle(x, y, x + w, y + h, outline=True, color=t.border)
    text_color = t.text_dim if not enabled else t.text if color is None else color
    gui_label(
        x + max(4, (w - engine.text_width(text)) / 2),
        y + (h - engine.text_height("Ag")) / 2,
        text,
        text_color,
        max_width=w - 8,
    )
    return hover and _take_click()


def gui_selectable(
    x: float, y: float, w: float, h: float, selected: bool = False
) -> bool:
    """A clickable row or cell, with nothing in it: draw on top. True on the frame it's clicked."""
    t = gui_theme
    hover = _widget_has_mouse(x, y, w, h)
    if selected or hover:
        _ctx.engine.draw_rectangle(
            x, y, x + w, y + h, color=t.button_hover if hover else t.button
        )
    return hover and _take_click()


def gui_progress_bar(
    x: float,
    y: float,
    w: float,
    h: float,
    fraction: float,
    color: Color,
    text: str = "",
) -> None:
    t = gui_theme
    engine = _ctx.engine
    fraction = max(0.0, min(1.0, fraction))
    engine.draw_rectangle(x, y, x + w, y + h, color=t.bar_back)
    if fraction > 0:
        engine.draw_rectangle(x, y, x + w * fraction, y + h, color=color)
    engine.draw_rectangle(x, y, x + w, y + h, outline=True, color=t.border)
    if text:
        engine.draw_text(
            x + (w - engine.text_width(text)) / 2,
            y + (h - engine.text_height(text)) / 2,
            text,
            t.text,
        )


def gui_text_input(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    focused: bool = True,
    hint: str = "",
    secret: bool = False,
) -> str:
    """
    Draw a text field and return its text, edited by whatever was typed this frame if it's
    `focused`. The caller owns the text, and which field has the focus.
    """
    t = gui_theme
    engine = _ctx.engine
    cursor = min(_state.cursors.get(id, len(text)), len(text))
    if focused:
        typed = "".join(ch for ch in keyboard_string() if ch.isprintable())
        if typed:
            text = text[:cursor] + typed + text[cursor:]
            cursor += len(typed)
        if keyboard_check_repeat(vk_backspace) and cursor > 0:
            text = text[: cursor - 1] + text[cursor:]
            cursor -= 1
        if keyboard_check_repeat(vk_delete) and cursor < len(text):
            text = text[:cursor] + text[cursor + 1 :]
        if keyboard_check_repeat(vk_left):
            cursor = max(0, cursor - 1)
        if keyboard_check_repeat(vk_right):
            cursor = min(len(text), cursor + 1)
        if keyboard_check_repeat(vk_home):
            cursor = 0
        if keyboard_check_repeat(vk_end):
            cursor = len(text)
    _state.cursors[id] = cursor

    engine.draw_rectangle(x, y, x + w, y + h, color=t.field_back)
    engine.draw_rectangle(
        x, y, x + w, y + h, outline=True, color=t.field_focus if focused else t.border
    )
    pad = 4
    shown = "*" * len(text) if secret else text
    text_y = y + (h - engine.text_height("Ag")) / 2
    engine.draw_set_clip(x + 1, y + 1, w - 2, h - 2)
    if not shown and hint and not focused:
        engine.draw_text(x + pad, text_y, hint, t.text_dim)
    # Scrolled along so the cursor is always in view.
    before = engine.text_width(shown[:cursor]) if cursor else 0
    scroll = max(0, before - (w - 2 * pad - 2))
    if shown:
        engine.draw_text(x + pad - scroll, text_y, shown, t.text)
    if focused and pg.time.get_ticks() % 1000 < 600:
        cursor_x = x + pad - scroll + before
        engine.draw_line(cursor_x, text_y, cursor_x, text_y + engine.text_height("Ag"), t.text)
    engine.draw_reset_clip()
    return text


def gui_scroll_area(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    content_height: float,
    wheel_step: float = 32,
    stick_to_bottom: bool = False,
) -> float:
    """
    Start a scrolling region and return the y to draw its content from. Drawing is clipped to it
    until `gui_end_scroll_area()`. With `stick_to_bottom` it follows new content (a chat log)
    unless the player has scrolled up.
    """
    excess = max(0.0, content_height - h)
    if stick_to_bottom:
        # Stored as distance from the bottom, so new content doesn't move what they're reading.
        from_bottom = _state.scroll_offsets.get(id, 0.0)
        if gui_mouse_in_rect(x, y, w, h):
            if mouse_wheel_up():
                from_bottom += wheel_step
            if mouse_wheel_down():
                from_bottom -= wheel_step
        from_bottom = max(0.0, min(excess, from_bottom))
        _state.scroll_offsets[id] = from_bottom
        offset = excess - from_bottom
    else:
        offset = _state.scroll_offsets.get(id, 0.0)
        if gui_mouse_in_rect(x, y, w, h):
            if mouse_wheel_up():
                offset -= wheel_step
            if mouse_wheel_down():
                offset += wheel_step
        offset = max(0.0, min(excess, offset))
        _state.scroll_offsets[id] = offset

    if excess > 0:
        t = gui_theme
        bar_h = max(16.0, h * h / content_height)
        bar_y = y + (h - bar_h) * (offset / excess)
        _ctx.engine.draw_rectangle(x + w - 3, bar_y, x + w, bar_y + bar_h, color=t.border)

    _state.scroll_stack.append((id, (x, y, w, h), offset))
    _ctx.engine.draw_set_clip(x, y, w, h)
    return y - offset


def gui_end_scroll_area() -> None:
    if _state.scroll_stack:
        _ = _state.scroll_stack.pop()
    _ctx.engine.draw_reset_clip()
