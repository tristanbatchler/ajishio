from __future__ import annotations
import colorsys
import pygame as pg
from ajishio.view import _view
from ajishio.sprite_loader import GameSprite


class Renderer:
    _instance: Renderer | None = None

    def __new__(cls) -> Renderer:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._screen: pg.Surface
        self.set_screen_size(
            _view.view_wport[_view.view_current], _view.view_hport[_view.view_current]
        )
        self._display: pg.Surface
        self._background_images: list[pg.Surface] = []

        self.draw_color: pg.Color = pg.Color(255, 255, 255)
        self.draw_font: pg.font.Font = pg.font.Font(None, 32)

    def set_screen_size(self, w: float, h: float) -> None:
        self._screen = pg.display.set_mode((w, h))

    def draw_display(self) -> None:
        scaled_display: pg.Surface = pg.transform.scale(self._display, self._screen.get_size())
        self._screen.blit(scaled_display, (0, 0))

    def fit_display(self) -> None:
        self._display = pg.Surface(
            (_view.view_wport[_view.view_current], _view.view_hport[_view.view_current]),
            flags=pg.SRCALPHA,
        )

    def fill_background_color(self, color: pg.Color) -> None:
        self._display.fill(color)

    def set_background_images(self, surfaces: list[pg.Surface]) -> None:
        self._background_images = surfaces

    def draw_background_images(self) -> None:
        for bg in self._background_images:
            self._display.blit(bg, _view.offset)


_renderer: Renderer = Renderer()

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


def _translate_offset(x: float, y: float) -> tuple[float, float]:
    return (x + _view.offset[0], y + _view.offset[1])


def make_color_hsv(hue: float, sat: float, val: float) -> Color:
    return Color(*[int(c * 255) for c in colorsys.hsv_to_rgb(hue, sat, val)])


def draw_circle(x: float, y: float, radius: float, color: Color | None = None) -> None:
    x, y = _translate_offset(x, y)
    pg.draw.circle(
        _renderer._display,
        _renderer.draw_color if color is None else color,
        (x, y),
        radius,
    )


def draw_rectangle(
    x: float,
    y: float,
    width: float,
    height: float,
    outline: bool = False,
    color: Color | None = None,
    alpha: float = 1.0,
) -> None:
    x, y = _translate_offset(x, y)
    color = _renderer.draw_color if color is None else color
    color.a = int(alpha * 255)
    rect_surf = pg.Surface((width, height), flags=pg.SRCALPHA)
    if outline:
        pg.draw.rect(rect_surf, color, (0, 0, width, height), 1)
    else:
        rect_surf.fill(color)
        _renderer._display.blit(rect_surf, (x, y))


def draw_line(x1: float, y1: float, x2: float, y2: float, color: Color | None = None) -> None:
    x1, y1 = _translate_offset(x1, y1)
    x2, y2 = _translate_offset(x2, y2)
    pg.draw.line(
        _renderer._display,
        _renderer.draw_color if color is None else color,
        (x1, y1),
        (x2, y2),
    )


def draw_text(x: float, y: float, string: str, color: Color | None = None) -> None:
    x, y = _translate_offset(x, y)
    text = _renderer.draw_font.render(
        string, True, _renderer.draw_color if color is None else color
    )
    _renderer._display.blit(text, (x, y))


def text_width(string: str) -> int:
    return _renderer.draw_font.size(string)[0]


def text_height(string: str) -> int:
    return _renderer.draw_font.size(string)[1]


def draw_sprite(
    x: float,
    y: float,
    sprite_index: GameSprite,
    image_index: int,
    x_scale: float = 1.0,
    y_scale: float = 1.0,
    rotation: float = 0.0,
    color: Color = c_white,
    alpha: float = 1.0,
) -> None:
    x, y = _translate_offset(x, y)
    image = sprite_index.images[image_index]
    if rotation != 0.0:
        image = pg.transform.rotate(image, rotation)
    if x_scale != 1.0 or y_scale != 1.0:
        image = pg.transform.scale(
            image, (int(image.get_width() * x_scale), int(image.get_height() * y_scale))
        )
    image.set_alpha(int(alpha * 255))
    if color != c_white:
        image.fill(color, special_flags=pg.BLEND_MULT)
    _renderer._display.blit(image, (x, y))
