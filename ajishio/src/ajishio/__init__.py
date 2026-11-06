from __future__ import annotations

from typing import TYPE_CHECKING, Callable, cast

import pygame as _pg

import os as _os
import ajishio._context as _ctx
from ajishio.view import view
from ajishio.rendering import Renderer
from ajishio.engine import Engine, set_window_icon

# --- Public class / type exports ---
from ajishio.game_object import GameObject
from ajishio.types import (
    GameSprite,
    GameLevel,
    CollisionMask,
    IGameObject,
    Entity,
    CustomFields,
    GameObjectKwargs,
)
from ajishio.game_sound import GameSound
from ajishio.rendering import Color, Font
from ajishio.net import GameNetClient, HttpResponse, http_request, run_task
from ajishio.tilemap import Tilemap
from ajishio.browser import (
    is_browser,
    browser_query_param,
    browser_storage_get,
    browser_storage_set,
)

# --- Input ---
from ajishio.input import (
    keyboard_check,
    keyboard_check_pressed,
    keyboard_check_released,
    keyboard_check_repeat,
    keyboard_string,
    input_activity,
    mouse_check_button,
    mouse_check_button_pressed,
    mouse_check_button_released,
    mouse_wheel_up,
    mouse_wheel_down,
    ord,
    vk_left,
    vk_right,
    vk_up,
    vk_down,
    vk_space,
    vk_escape,
    vk_enter,
    vk_backspace,
    vk_tab,
    vk_delete,
    vk_home,
    vk_end,
    vk_pageup,
    vk_pagedown,
    vk_shift,
    vk_control,
    mb_left,
    mb_middle,
    mb_right,
)

# --- Immediate-mode GUI (call from draw_gui) ---
from ajishio.ui import end_frame as _ui_end_frame
from ajishio.ui import (
    GuiTheme,
    gui_theme,
    gui_panel,
    gui_button,
    gui_selectable,
    gui_label,
    gui_label_wrapped,
    gui_progress_bar,
    gui_text_input,
    gui_scroll_area,
    gui_end_scroll_area,
    gui_mouse_over,
    gui_mouse_in_rect,
)

# --- Utils ---
from ajishio.utils import (
    lengthdir_x,
    lengthdir_y,
    clamp,
    sign,
    lerp,
    point_distance,
    map_value,
    room_set_caption,
    profile,
)

# --- Rendering: color constants and free functions ---
from ajishio.rendering import (
    c_aqua,
    c_black,
    c_blue,
    c_dkgray,
    c_fuchsia,
    c_gray,
    c_green,
    c_lime,
    c_ltgray,
    c_maroon,
    c_navy,
    c_olive,
    c_orange,
    c_purple,
    c_red,
    c_silver,
    c_teal,
    c_white,
    c_yellow,
    make_color_hsv,
    load_font,
)


# --- Asset loaders ---
from ajishio.sprite_loader import (
    load_aseprite_sprites,
    load_aseprite_sprite,
    load_sprite_from_sheet,
    sprite_set_offset,
)
from ajishio.sound_loader import load_sounds, load_sound
from ajishio.level_loader import load_ldtk_levels

# --- Singleton instantiation (must happen before any game logic runs) ---
if _os.environ.get("AJISHIO_DOCS"):
    # Documentation mode: use lightweight dummies that won't open a window
    class _Dummy:
        def __getattr__(self, name: str) -> Callable[..., None]:
            return lambda *args, **kwargs: None

    _renderer: Renderer = cast(Renderer, cast(object, _Dummy()))
    _gui_renderer: Renderer = cast(Renderer, cast(object, _Dummy()))
    _engine: Engine = cast(Engine, cast(object, _Dummy()))
else:
    _ = _pg.init()
    _renderer = Renderer(use_view_offset=True)
    _gui_renderer = Renderer(use_view_offset=False)

    set_window_icon()
    _pg.display.set_caption("Ajishio Game")
    _engine = Engine(_renderer, _gui_renderer)

# Populate the lazy context so game_object / game_sound can access the engine.
_ctx.engine = _engine

_engine.after_gui_pass = _ui_end_frame

Surface = _pg.Surface

# --- Rendering: methods are on the engine, but in turn call methods on either of its renderers ---
draw_set_color = _engine.draw_set_color
draw_set_circle_precision = _engine.draw_set_circle_precision
draw_circle = _engine.draw_circle
draw_ellipse = _engine.draw_ellipse
draw_rectangle = _engine.draw_rectangle
draw_triangle = _engine.draw_triangle
draw_point = _engine.draw_point
draw_line = _engine.draw_line
draw_text = _engine.draw_text
draw_sprite = _engine.draw_sprite
draw_set_font = _engine.draw_set_font
text_width = _engine.text_width
text_height = _engine.text_height
text_wrap = _engine.text_wrap
draw_surface = _engine.draw_surface
draw_set_clip = _engine.draw_set_clip
draw_reset_clip = _engine.draw_reset_clip

# --- View: bound methods delegated through engine so the renderer stays in sync ---
view_set_wport = _engine.view_set_wport
view_set_hport = _engine.view_set_hport
view_set_xport = _engine.view_set_xport
view_set_yport = _engine.view_set_yport
view_set_zoom = _engine.view_set_zoom
window_set_size = _engine.window_set_size
window_set_resizable = _engine.window_set_resizable
window_to_room = _engine.window_to_room
room_to_window = _engine.room_to_window

# These are mutable dicts — exporting a reference is safe; mutations are shared.
view_xport = view.view_xport
view_yport = view.view_yport
view_wport = view.view_wport
view_hport = view.view_hport

# --- Engine method delegates ---
game_start = _engine.game_start
game_start_async = _engine.game_start_async
game_end = _engine.game_end
game_restart = _engine.game_restart
game_set_speed = _engine.game_set_speed
set_rooms = _engine.set_rooms
add_object = _engine.add_object
register_objects = _engine.register_objects
room_goto = _engine.room_goto
room_goto_next = _engine.room_goto_next
room_goto_previous = _engine.room_goto_previous
room_restart = _engine.room_restart

room_set_size: Callable[[float, float], None] = _engine.room_set_size
"""Sets the size of the room. This does not affect the window size or viewport."""

room_set_width = _engine.room_set_width
room_set_height = _engine.room_set_height
room_set_background = _engine.room_set_background
instance_destroy = _engine.instance_destroy
instance_count = _engine.instance_count
instance_exists = _engine.instance_exists
instance_position = _engine.instance_position
instance_find = _engine.instance_find
instances_iterate = _engine.instances_iterate
collision_rectangle = _engine.collision_rectangle
collision_rectangle_list = _engine.collision_rectangle_list
audio_play_sound = _engine.audio_play_sound
audio_is_playing = _engine.audio_is_playing

# --- Live engine properties (change every frame) ---
_LIVE_ENGINE_ATTRS = frozenset(
    {
        "room_width",
        "room_height",
        "room_speed",
        "room_background_color",
        "delta_time",
        "fps_real",
        "room",
        "mouse_x",
        "mouse_y",
        "mouse_room_x",
        "mouse_room_y",
    }
)

_LIVE_VIEW_ATTRS = frozenset(
    {
        "view_current",
        "window_width",
        "window_height",
    }
)


def __getattr__(name: str) -> object:
    if name in _LIVE_ENGINE_ATTRS:
        try:
            return getattr(_engine, name)  # pyright: ignore[reportAny]
        except AttributeError:
            raise AttributeError(f"module 'ajishio' has no attribute {name!r}")
    if name in _LIVE_VIEW_ATTRS:
        return getattr(view, name)  # pyright: ignore[reportAny]
    raise AttributeError(f"module 'ajishio' has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(__all__)


if TYPE_CHECKING:
    room_width: float
    room_height: float
    room_speed: float
    room_background_color: Color
    delta_time: float
    fps_real: float
    room: int

    view_current: int
    window_width: int
    window_height: int
    mouse_x: float
    mouse_y: float
    mouse_room_x: float
    mouse_room_y: float


__all__ = [
    # Classes / types
    "GameObject",
    "GameSprite",
    "GameLevel",
    "CollisionMask",
    "IGameObject",
    "Entity",
    "CustomFields",
    "GameObjectKwargs",
    "GameSound",
    "GameNetClient",
    "HttpResponse",
    "http_request",
    "run_task",
    "Tilemap",
    "is_browser",
    "browser_query_param",
    "browser_storage_get",
    "browser_storage_set",
    "Color",
    "Font",
    "Surface",
    # Input
    "keyboard_check",
    "keyboard_check_pressed",
    "keyboard_check_released",
    "keyboard_check_repeat",
    "keyboard_string",
    "input_activity",
    "mouse_check_button",
    "mouse_check_button_pressed",
    "mouse_check_button_released",
    "mouse_wheel_up",
    "mouse_wheel_down",
    "ord",
    "vk_left",
    "vk_right",
    "vk_up",
    "vk_down",
    "vk_space",
    "vk_escape",
    "vk_enter",
    "vk_backspace",
    "vk_tab",
    "vk_delete",
    "vk_home",
    "vk_end",
    "vk_pageup",
    "vk_pagedown",
    "vk_shift",
    "vk_control",
    "mb_left",
    "mb_middle",
    "mb_right",
    # Utils
    "lengthdir_x",
    "lengthdir_y",
    "clamp",
    "sign",
    "lerp",
    "profile",
    "point_distance",
    "map_value",
    "room_set_caption",
    # Colors
    "c_aqua",
    "c_black",
    "c_blue",
    "c_dkgray",
    "c_fuchsia",
    "c_gray",
    "c_green",
    "c_lime",
    "c_ltgray",
    "c_maroon",
    "c_navy",
    "c_olive",
    "c_orange",
    "c_purple",
    "c_red",
    "c_silver",
    "c_teal",
    "c_white",
    "c_yellow",
    "make_color_hsv",
    "load_font",
    # Drawing
    "draw_set_color",
    "draw_set_circle_precision",
    "draw_circle",
    "draw_ellipse",
    "draw_rectangle",
    "draw_triangle",
    "draw_point",
    "draw_line",
    "draw_text",
    "draw_sprite",
    "draw_set_font",
    "text_width",
    "text_height",
    "text_wrap",
    "draw_surface",
    "draw_set_clip",
    "draw_reset_clip",
    # GUI
    "GuiTheme",
    "gui_theme",
    "gui_panel",
    "gui_button",
    "gui_selectable",
    "gui_label",
    "gui_label_wrapped",
    "gui_progress_bar",
    "gui_text_input",
    "gui_scroll_area",
    "gui_end_scroll_area",
    "gui_mouse_over",
    "gui_mouse_in_rect",
    # View
    "view_set_wport",
    "view_set_hport",
    "view_set_xport",
    "view_set_yport",
    "view_set_zoom",
    "window_set_size",
    "window_set_resizable",
    "window_to_room",
    "room_to_window",
    "view_xport",
    "view_yport",
    "view_wport",
    "view_hport",
    # Loaders
    "load_aseprite_sprites",
    "load_aseprite_sprite",
    "load_sprite_from_sheet",
    "sprite_set_offset",
    "load_sounds",
    "load_sound",
    "load_ldtk_levels",
    # Engine methods
    "game_start",
    "game_start_async",
    "game_end",
    "game_restart",
    "game_set_speed",
    "set_rooms",
    "register_objects",
    "room_goto",
    "room_goto_next",
    "room_goto_previous",
    "room_restart",
    "room_set_size",
    "room_set_width",
    "room_set_height",
    "room_set_background",
    "instance_destroy",
    "instance_count",
    "instance_exists",
    "instance_position",
    "instance_find",
    "instances_iterate",
    "collision_rectangle",
    "collision_rectangle_list",
    "audio_play_sound",
    "audio_is_playing",
    # Live properties (resolved via __getattr__)
    "room_width",
    "room_height",
    "room_speed",
    "room_background_color",
    "delta_time",
    "fps_real",
    "room",
    "view_current",
    "window_width",
    "window_height",
    "mouse_x",
    "mouse_y",
    "mouse_room_x",
    "mouse_room_y",
]
