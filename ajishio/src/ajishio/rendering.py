from pygame.surface import Surface


from collections.abc import Iterable
import colorsys
from pathlib import Path
import pygame as pg
from ajishio.view import view
from ajishio.types import GameSprite

Color = pg.Color


c_aqua = Color(0, 255, 255)
c_black = Color(0, 0, 0)
c_blue = Color(0, 0, 255)
c_dkgray = Color(64, 64, 64)
c_fuchsia = Color(255, 0, 255)
c_gray = Color(128, 128, 128)
c_green = Color(0, 128, 0)
c_lime = Color(0, 255, 0)
c_ltgray = Color(192, 192, 192)
c_maroon = Color(128, 0, 0)
c_navy = Color(0, 0, 128)
c_olive = Color(128, 128, 0)
c_orange = Color(255, 160, 64)
c_purple = Color(128, 0, 128)
c_red = Color(255, 0, 0)
c_silver = Color(192, 192, 192)
c_teal = Color(0, 128, 128)
c_white = Color(255, 255, 255)
c_yellow = Color(255, 255, 0)


def _translate_offset(x: float, y: float) -> tuple[float, float]:
    return (x + view.offset[0], y + view.offset[1])


def make_color_hsv(hue: float, sat: float, val: float) -> Color:
    return Color(*[int(c * 255) for c in colorsys.hsv_to_rgb(hue, sat, val)])


def load_font(font_path: Path | str, size: int) -> pg.font.Font:
    try:
        return pg.font.Font(str(font_path), size)
    except FileNotFoundError:
        return pg.font.Font(None, size)


class Renderer:
    def __init__(self) -> None:
        self._screen: pg.Surface | None = None
        self.set_screen_size(view.window_width, view.window_height)
        self.fit_display()
        self._background_images: Iterable[pg.Surface] = []

        self.draw_color: Color = Color(255, 255, 255)
        self.draw_font: pg.font.Font = pg.font.Font(None, 32)
        self.draw_font_fallbacks: Iterable[pg.font.Font] = []

    def set_screen_size(self, w: float, h: float) -> None:
        self._screen = pg.display.set_mode((w, h))

    def draw_display(self) -> None:
        if self._screen is None:
            return
        scaled_display: pg.Surface = pg.transform.scale(self.display, self._screen.get_size())
        _ = self._screen.blit(scaled_display, (0, 0))

    def fit_display(self) -> None:
        self.display: Surface = pg.Surface(
            (view.view_wport[view.view_current], view.view_hport[view.view_current]),
            flags=pg.SRCALPHA,
        )

    def fill_background_color(self, color: pg.Color) -> None:
        _ = self.display.fill(color)

    def set_background_images(self, surfaces: Iterable[pg.Surface]) -> None:
        self._background_images = surfaces

    def draw_background_images(self) -> None:
        for bg in self._background_images:
            _ = self.display.blit(bg, view.offset)

    def draw_circle(self, x: float, y: float, radius: float, color: pg.Color | None = None) -> None:
        x, y = _translate_offset(x, y)
        _ = pg.draw.circle(
            self.display,
            self.draw_color if color is None else color,
            (x, y),
            radius,
        )

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        outline: bool = False,
        color: pg.Color | None = None,
        alpha: float = 1.0,
    ) -> None:
        x, y = _translate_offset(x, y)
        color = self.draw_color if color is None else color
        color.a = int(alpha * 255)
        rect_surf = pg.Surface((width, height), flags=pg.SRCALPHA)
        if outline:
            _ = pg.draw.rect(rect_surf, color, (0, 0, width, height), 1)
        else:
            _ = rect_surf.fill(color)
        _ = self.display.blit(rect_surf, (x, y))

    def draw_line(
        self, x1: float, y1: float, x2: float, y2: float, color: pg.Color | None = None
    ) -> None:
        x1, y1 = _translate_offset(x1, y1)
        x2, y2 = _translate_offset(x2, y2)
        _ = pg.draw.line(
            self.display,
            self.draw_color if color is None else color,
            (x1, y1),
            (x2, y2),
        )

    def draw_text(self, x: float, y: float, string: str, color: pg.Color | None = None) -> None:
        x, y = _translate_offset(x, y)
        surface = self._render_text_with_fallback(
            string, self.draw_color if color is None else color
        )
        _ = self.display.blit(surface, (x, y))

    def text_width(self, string: str) -> int:
        return self._render_text_with_fallback(string, self.draw_color).get_width()

    def text_height(self, string: str) -> int:
        return self._render_text_with_fallback(string, self.draw_color).get_height()

    def draw_sprite(
        self,
        x: float,
        y: float,
        sprite_index: GameSprite,
        image_index: int,
        x_scale: float = 1.0,
        y_scale: float = 1.0,
        rotation: float = 0.0,
        color: pg.Color = c_white,
        alpha: float = 1.0,
    ) -> None:
        if x_scale == 0.0 or y_scale == 0.0:
            return

        scale_x_abs: float = abs(x_scale)
        scale_y_abs: float = abs(y_scale)

        offset_x: float = (
            sprite_index.x_offset if x_scale >= 0 else sprite_index.width - sprite_index.x_offset
        )
        offset_y: float = (
            sprite_index.y_offset if y_scale >= 0 else sprite_index.height - sprite_index.y_offset
        )

        draw_x: float = x - offset_x * scale_x_abs
        draw_y: float = y - offset_y * scale_y_abs
        draw_x, draw_y = _translate_offset(draw_x, draw_y)
        image_index = image_index % len(sprite_index.images)
        image = sprite_index.images[image_index]
        if rotation != 0.0:
            image = pg.transform.rotate(image, rotation)

        if x_scale != 1.0 or y_scale != 1.0:
            image = pg.transform.scale(
                image,
                (
                    int(image.get_width() * scale_x_abs),
                    int(image.get_height() * scale_y_abs),
                ),
            )
            image = pg.transform.flip(image, x_scale < 0, y_scale < 0)
        image.set_alpha(int(alpha * 255))
        if color != c_white:
            _ = image.fill(color, special_flags=pg.BLEND_MULT)
        _ = self.display.blit(image, (draw_x, draw_y))

    def draw_set_font(
        self, font: pg.font.Font, fallbacks: Iterable[pg.font.Font] | None = None
    ) -> None:
        self.draw_font = font
        self.draw_font_fallbacks = [] if fallbacks is None else fallbacks

    def _pick_font_for_char(self, char: str) -> pg.font.Font:
        for font in [self.draw_font, *self.draw_font_fallbacks]:
            glyph_surface = font.render(char, True, self.draw_color)
            tofu_surface = font.render("□", True, self.draw_color)
            if glyph_surface.get_size() == tofu_surface.get_size():
                if pg.image.tobytes(glyph_surface, "RGBA") == pg.image.tobytes(
                    tofu_surface, "RGBA"
                ):
                    continue
            return font
        return self.draw_font

    def _render_text_with_fallback(self, string: str, color: pg.Color) -> pg.Surface:
        if not string:
            return pg.Surface((0, 0), flags=pg.SRCALPHA)

        glyphs: list[tuple[pg.Surface, int]] = []
        cursor_x = 0
        max_h = 0
        for ch in string:
            font = self._pick_font_for_char(ch)
            glyph_surface = font.render(ch, True, color)
            glyphs.append((glyph_surface, cursor_x))
            cursor_x += glyph_surface.get_width()
            if glyph_surface.get_height() > max_h:
                max_h = glyph_surface.get_height()

        rendered = pg.Surface((cursor_x, max_h), flags=pg.SRCALPHA)
        for glyph_surface, gx in glyphs:
            _ = rendered.blit(glyph_surface, (gx, max_h - glyph_surface.get_height()))
        return rendered
