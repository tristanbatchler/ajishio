import colorsys
import pygame as pg
from ajishio.engine import _engine
from ajishio.view import _view

Color = pg.Color

c_aqua: Color = Color(0, 255, 255)
c_black: Color = Color(0, 0, 0)
c_blue: Color = Color(0, 0, 255)
c_dkgray: Color = Color(64, 64, 64)
c_fuchsia: Color = Color(255, 0, 255)
c_gray: Color = Color(128, 128, 128)
c_green: Color = Color(0, 128, 0)
c_lime: Color = Color(0, 255, 0)
c_ltgray: Color = Color(192, 192, 192)
c_maroon: Color = Color(128, 0, 0)
c_navy: Color = Color(0, 0, 128)
c_olive: Color = Color(128, 128, 0)
c_orange: Color = Color(255, 160, 64)
c_purple: Color = Color(128, 0, 128)
c_red: Color = Color(255, 0, 0)
c_silver: Color = Color(192, 192, 192)
c_teal: Color = Color(0, 128, 128)
c_white: Color = Color(255, 255, 255)
c_yellow: Color = Color(255, 255, 0)

_draw_color: Color = Color(255, 255, 255)
_draw_font: pg.font.Font = pg.font.Font(None, 32)

def _translate_offset(x: float, y: float) -> tuple[float, float]:
    return (x + _view.offset[0], y + _view.offset[1])

def make_color_hsv(hue: float, sat: float, val: float) -> Color:
    return Color(*[int(c * 255) for c in colorsys.hsv_to_rgb(hue, sat, val)])

def draw_circle(x: float, y: float, radius: float, color: Color | None = None) -> None:
    x, y =_translate_offset(x, y)
    pg.draw.circle(_engine._get_display(), _draw_color if color is None else color, (x, y), radius)

def draw_rectangle(x: float, y: float, room_width: float, room_height: float, outline: bool = False, color: Color | None = None) -> None:
    x, y = _translate_offset(x, y)
    pg.draw.rect(_engine._get_display(), _draw_color if color is None else color, (x, y, room_width, room_height), int(outline))

def draw_line(x1: float, y1: float, x2: float, y2: float, color: Color | None = None) -> None:
    x1, y1 =_translate_offset(x1, y1)
    x2, y2 =_translate_offset(x2, y2)
    pg.draw.line(_engine._get_display(), _draw_color if color is None else color, (x1, y1), (x2, y2))

def draw_text(x: float, y: float, string: str, color: Color | None = None) -> None:
    x, y =_translate_offset(x, y)
    text = _draw_font.render(string, True, _draw_color if color is None else color)
    _engine._get_display().blit(text, (x, y))

def text_width(string: str) -> int:
    return _draw_font.size(string)[0]

def text_height(string: str) -> int:
    return _draw_font.size(string)[1]