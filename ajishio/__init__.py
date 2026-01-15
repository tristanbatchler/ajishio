from __future__ import annotations

import sys
from types import ModuleType
from typing import Literal, TYPE_CHECKING, overload

from pygame import init as pg_init

# Initialise pygame first as the rest of our modules may depend on it
pg_init()

# Import engine and subsystems without star-imports; public API is provided
# dynamically via __getattr__ so that demo code can continue to use
# `import ajishio as aj` and call functions directly.
from ajishio import engine as _engine_module  # noqa: E402
from ajishio import game_object as _game_object_module  # noqa: E402
from ajishio import game_sound as _game_sound_module  # noqa: E402
from ajishio import input as _input_module  # noqa: E402
from ajishio import level_loader as _level_loader_module  # noqa: E402
from ajishio import rendering as _rendering_module  # noqa: E402
from ajishio import sound_loader as _sound_loader_module  # noqa: E402
from ajishio import sprite_loader as _sprite_loader_module  # noqa: E402
from ajishio import utils as _utils_module  # noqa: E402
from ajishio import view as _view_module  # noqa: E402

from ajishio.engine import (  # noqa: E402
    _engine,
    audio_is_playing,
    audio_play_sound,
    game_end,
    game_restart,
    game_set_speed,
    game_start,
    instance_count,
    instance_destroy,
    instance_exists,
    instance_find,
    register_objects,
    room_goto,
    room_goto_next,
    room_goto_previous,
    room_restart,
    room_set_background,
    room_set_height,
    room_set_size,
    room_set_width,
    set_rooms,
)
from ajishio.game_object import CollisionMask, GameObject  # noqa: E402
from ajishio.game_sound import GameSound  # noqa: E402
from ajishio.input import (  # noqa: E402
    QuitInterrupt,
    keyboard_check,
    keyboard_check_pressed,
    keyboard_check_released,
    ord as key_ord,
    vk_down,
    vk_enter,
    vk_escape,
    vk_left,
    vk_right,
    vk_space,
    vk_up,
)
from ajishio.level_loader import GameLevel, load_ldtk, load_ldtk_levels  # noqa: E402
from ajishio.rendering import (  # noqa: E402
    Color,
    _renderer,
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
    draw_circle,
    draw_line,
    draw_rectangle,
    draw_sprite,
    draw_text,
    draw_set_font,
    load_font,
    make_color_hsv,
    text_height,
    text_width,
)
from ajishio.sound_loader import load_sound, load_sounds  # noqa: E402
from ajishio.sprite_loader import GameSprite, load_aseprite_sprite, load_aseprite_sprites  # noqa: E402
from ajishio.utils import (  # noqa: E402
    clamp,
    lengthdir_x,
    lengthdir_y,
    lerp,
    map_value,
    point_distance,
    remove_ext,
    room_set_caption,
    sign,
)
from ajishio.view import (  # noqa: E402
    _view,
    view_set_hport,
    view_set_wport,
    view_set_xport,
    view_set_yport,
    window_set_size,
)

ord = key_ord

_MODULES: tuple[ModuleType, ...] = (
    _engine_module,
    _input_module,
    _game_sound_module,
    _rendering_module,
    _view_module,
    _level_loader_module,
    _sprite_loader_module,
    _sound_loader_module,
    _game_object_module,
    _utils_module,
)

__all__: tuple[str, ...] = (
    "_engine",
    "_renderer",
    "_view",
    "audio_is_playing",
    "audio_play_sound",
    "draw_set_font",
    "load_font",
    "clamp",
    "CollisionMask",
    "Color",
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
    "draw_circle",
    "draw_line",
    "draw_rectangle",
    "draw_sprite",
    "draw_text",
    "draw_set_font",
    "load_font",
    "GameObject",
    "GameLevel",
    "GameSound",
    "GameSprite",
    "game_end",
    "game_restart",
    "game_set_speed",
    "game_start",
    "instance_count",
    "instance_destroy",
    "instance_exists",
    "instance_find",
    "key_ord",
    "keyboard_check",
    "keyboard_check_pressed",
    "keyboard_check_released",
    "lengthdir_x",
    "lengthdir_y",
    "lerp",
    "load_ldtk",
    "load_ldtk_levels",
    "load_aseprite_sprite",
    "load_aseprite_sprites",
    "load_sound",
    "load_sounds",
    "make_color_hsv",
    "map_value",
    "ord",
    "point_distance",
    "QuitInterrupt",
    "register_objects",
    "remove_ext",
    "room_goto",
    "room_goto_next",
    "room_goto_previous",
    "room_restart",
    "room_set_background",
    "room_set_caption",
    "room_set_height",
    "room_set_size",
    "room_set_width",
    "set_rooms",
    "sign",
    "text_height",
    "text_width",
    "view_set_hport",
    "view_set_wport",
    "view_set_xport",
    "view_set_yport",
    "vk_down",
    "vk_enter",
    "vk_escape",
    "vk_left",
    "vk_right",
    "vk_space",
    "vk_up",
    "window_set_size",
)


if TYPE_CHECKING:
    delta_time: float
    fps_real: float
    room: int
    room_background_color: Color
    room_height: float
    room_speed: float
    room_width: float
    view_current: int
    view_hport: dict[int, float]
    view_wport: dict[int, float]
    view_xport: dict[int, float]
    view_yport: dict[int, float]
    window_height: int
    window_width: int


@overload
def __getattr__(name: Literal["room_width", "room_height", "room_speed", "delta_time", "fps_real"]) -> float: ...


@overload
def __getattr__(name: Literal["room"]) -> int: ...


@overload
def __getattr__(name: Literal["room_background_color"]) -> Color: ...


@overload
def __getattr__(name: Literal["view_current"]) -> int: ...


@overload
def __getattr__(
    name: Literal["view_xport", "view_yport", "view_wport", "view_hport"]
) -> dict[int, float]: ...


@overload
def __getattr__(name: Literal["window_width", "window_height"]) -> int: ...


@overload
def __getattr__(name: str) -> object: ...


def __getattr__(name: str) -> object:
    """Dynamically expose engine and subsystem attributes on the ajishio package."""
    module_globals = sys.modules[__name__].__dict__
    if name in module_globals:
        return module_globals[name]

    if name in _engine.__dict__:
        return getattr(_engine, name)

    if name in _view.__dict__:
        return getattr(_view, name)

    for module in _MODULES:
        if hasattr(module, name):
            return getattr(module, name)

    raise AttributeError(f"module 'ajishio' has no attribute '{name}'")
