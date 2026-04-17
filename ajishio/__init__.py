from __future__ import annotations

from typing import TYPE_CHECKING

import ajishio._context as _ctx
from ajishio.view import view
from ajishio.rendering import Renderer
from ajishio.engine import Engine

# --- Public class / type exports ---
from ajishio.game_object import GameObject
from ajishio.types import GameSprite, GameLevel, CollisionMask, IGameObject, Entity
from ajishio.game_sound import GameSound

# --- Input ---
from ajishio.input import (
    keyboard_check,
    keyboard_check_pressed,
    keyboard_check_released,
    ord,
    vk_left, vk_right, vk_up, vk_down,
    vk_space, vk_escape, vk_enter,
)

# --- Utils ---
from ajishio.utils import (
    lengthdir_x, lengthdir_y,
    clamp, sign, lerp,
    point_distance,
    map_value,
    room_set_caption,
)

# --- Rendering: color constants and free functions ---
from ajishio.rendering import (
    c_aqua, c_black, c_blue, c_dkgray, c_fuchsia, c_gray,
    c_green, c_lime, c_ltgray, c_maroon, c_navy, c_olive,
    c_orange, c_purple, c_red, c_silver, c_teal, c_white, c_yellow,
    make_color_hsv,
    load_font,
)

# --- Asset loaders ---
from ajishio.sprite_loader import load_aseprite_sprites, load_aseprite_sprite, sprite_set_offset
from ajishio.sound_loader import load_sounds, load_sound
from ajishio.level_loader import load_ldtk_levels

# --- Singleton instantiation (must happen before any game logic runs) ---
import pygame as _pg
_ = _pg.init()

_renderer = Renderer()
_engine = Engine(_renderer)

# Populate the lazy context so game_object / game_sound can access the engine.
_ctx.engine = _engine

# --- Rendering: bound methods on the renderer singleton ---
draw_circle    = _renderer.draw_circle
draw_rectangle = _renderer.draw_rectangle
draw_line      = _renderer.draw_line
draw_text      = _renderer.draw_text
draw_sprite    = _renderer.draw_sprite
draw_set_font  = _renderer.draw_set_font
text_width     = _renderer.text_width
text_height    = _renderer.text_height

# --- View: bound methods on the view singleton ---
view_set_wport  = view.view_set_wport
view_set_hport  = view.view_set_hport
view_set_xport  = view.view_set_xport
view_set_yport  = view.view_set_yport
window_set_size = view.window_set_size

# --- Engine method delegates ---
game_start          = _engine.game_start
game_end            = _engine.game_end
game_restart        = _engine.game_restart
game_set_speed      = _engine.game_set_speed
set_rooms           = _engine.set_rooms
register_objects    = _engine.register_objects
room_goto           = _engine.room_goto
room_goto_next      = _engine.room_goto_next
room_goto_previous  = _engine.room_goto_previous
room_restart        = _engine.room_restart
room_set_size       = _engine.room_set_size
room_set_width      = _engine.room_set_width
room_set_height     = _engine.room_set_height
room_set_background = _engine.room_set_background
instance_destroy    = _engine.instance_destroy
instance_count      = _engine.instance_count
instance_exists     = _engine.instance_exists
instance_find       = _engine.instance_find
audio_play_sound    = _engine.audio_play_sound
audio_is_playing    = _engine.audio_is_playing

# --- Live engine properties (change every frame) ---
def __getattr__(name: str) -> object:
    match name:
        case "room_width":
            return _engine.room_width
        case "room_height":
            return _engine.room_height
        case "room_speed":
            return _engine.room_speed
        case "room_background_color":
            return _engine.room_background_color
        case "delta_time":
            return _engine.delta_time
        case "fps_real":
            return _engine.fps_real
        case "room":
            return _engine.room
        case _:
            raise AttributeError(f"module 'ajishio' has no attribute {name!r}")


if TYPE_CHECKING:
    import pygame as pg

    room_width: float
    room_height: float
    room_speed: float
    room_background_color: pg.Color
    delta_time: float
    fps_real: float
    room: int


__all__ = [
    # Classes / types
    "GameObject", "GameSprite", "GameLevel", "CollisionMask", "IGameObject", "Entity",
    "GameSound",
    # Input
    "keyboard_check", "keyboard_check_pressed", "keyboard_check_released",
    "ord",
    "vk_left", "vk_right", "vk_up", "vk_down", "vk_space", "vk_escape", "vk_enter",
    # Utils
    "lengthdir_x", "lengthdir_y", "clamp", "sign", "lerp",
    "point_distance", "map_value", "room_set_caption",
    # Colors
    "c_aqua", "c_black", "c_blue", "c_dkgray", "c_fuchsia", "c_gray",
    "c_green", "c_lime", "c_ltgray", "c_maroon", "c_navy", "c_olive",
    "c_orange", "c_purple", "c_red", "c_silver", "c_teal", "c_white", "c_yellow",
    "make_color_hsv", "load_font",
    # Drawing
    "draw_circle", "draw_rectangle", "draw_line", "draw_text", "draw_sprite",
    "draw_set_font", "text_width", "text_height",
    # View
    "view_set_wport", "view_set_hport", "view_set_xport", "view_set_yport",
    "window_set_size",
    # Loaders
    "load_aseprite_sprites", "load_aseprite_sprite", "sprite_set_offset",
    "load_sounds", "load_sound", "load_ldtk_levels",
    # Engine methods
    "game_start", "game_end", "game_restart", "game_set_speed",
    "set_rooms", "register_objects",
    "room_goto", "room_goto_next", "room_goto_previous", "room_restart",
    "room_set_size", "room_set_width", "room_set_height", "room_set_background",
    "instance_destroy", "instance_count", "instance_exists", "instance_find",
    "audio_play_sound", "audio_is_playing",
    # Live properties (resolved via __getattr__)
    "room_width", "room_height", "room_speed", "room_background_color",
    "delta_time", "fps_real", "room",
]
