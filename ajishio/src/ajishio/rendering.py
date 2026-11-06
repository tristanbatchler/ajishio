from pygame.surface import Surface


from collections.abc import Iterable
import colorsys
from pathlib import Path
import pygame as pg
from ajishio.view import view
from ajishio.types import GameSprite
import math

Color = pg.Color
Font = pg.font.Font

_TEXT_CACHE_SIZE = 2048


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


def _color_with_alpha(color: Color, alpha: float) -> Color:
    clamped_alpha = max(0.0, min(1.0, alpha))
    return Color(color.r, color.g, color.b, int(clamped_alpha * 255))


def make_color_hsv(hue: float, sat: float, val: float) -> Color:
    return Color(*[int(c * 255) for c in colorsys.hsv_to_rgb(hue, sat, val)])


def load_font(font_path: Path | str, size: int) -> pg.font.Font:
    try:
        return pg.font.Font(str(font_path), size)
    except FileNotFoundError:
        return pg.font.Font(None, size)


class Renderer:
    def __init__(self, use_view_offset: bool) -> None:
        self.use_view_offset: bool = use_view_offset
        self._screen: pg.Surface | None = None
        self.set_screen_size(view.window_width, view.window_height)
        self.fit_display()
        self._background_images: Iterable[pg.Surface] = []

        self.draw_color: Color = Color(255, 255, 255)
        self.draw_circle_precision: int = 24
        self.draw_font: pg.font.Font = pg.font.Font(None, 32)
        self.draw_font_fallbacks: Iterable[pg.font.Font] = []
        self._text_cache: dict[
            tuple[
                pg.font.Font,
                tuple[bool, bool, bool],
                tuple[pg.font.Font, ...],
                str,
                tuple[int, int, int, int],
            ],
            pg.Surface,
        ] = {}

    def _translate_offset(self, x: float, y: float) -> tuple[float, float]:
        if not self.use_view_offset:
            return (x, y)
        return (x + view.offset[0], y + view.offset[1])

    def draw_set_color(self, color: Color) -> None:
        """
        With this function you can set the base draw color for the game.
        This will affect drawing of fonts, forms, primitives and 3D, however it will not affect
        sprites (drawn manually or by an instance). If any affected graphics are drawn with their
        own color values, this value will be ignored.

        Args:
            color: The color to set for drawing.
        """
        self.draw_color = color

    def draw_set_circle_precision(self, precision: int) -> None:
        """
        To optimise performance when drawing circles, Ajishio basically draws a polygon shape with
        enough sides to make it appear circular. However, depending on how big or small you need
        your circles to be, you may find that changing this value can help increase the performance
        of your game, or make the circles look better. The precision value that you can input into
        this function is the number of sides the circle polygon has, and this number can be anything
        between 4 and 64, but must be a number divisible by 4, with a default value of 24.
        """
        if precision < 4 or precision > 64 or precision % 4 != 0:
            raise ValueError(
                "Circle precision must be a number between 4 and 64, divisible by 4."
            )
        self.draw_circle_precision = precision

    def set_screen_size(self, w: float, h: float, flags: int = 0) -> None:
        self._screen = pg.display.set_mode((w, h), flags)

    def refresh_screen(self) -> None:
        """Pick up the window surface again after the OS resized the window."""
        self._screen = pg.display.get_surface()

    def display_transform(self) -> tuple[float, int, int]:
        """
        How `display` lands in the window: (scale, left, top). It fits the window's current size,
        or, with a zoom set (`view_set_zoom`), is drawn at exactly that scale.
        """
        if self._screen is None:
            return (1.0, 0, 0)
        win_w, win_h = self._screen.get_size()
        disp_w, disp_h = self.display.get_size()
        if disp_w == 0 or disp_h == 0:
            return (1.0, 0, 0)
        zoom = view.view_zoom.get(view.view_current) if self.use_view_offset else None
        scale: float = zoom if zoom is not None else min(win_w / disp_w, win_h / disp_h)
        return (
            scale,
            (win_w - int(disp_w * scale)) // 2,
            (win_h - int(disp_h * scale)) // 2,
        )

    def window_to_room(self, x: float, y: float) -> tuple[float, float]:
        """Convert a window pixel position to room coordinates.

        Inverse of what ``draw_display`` does: undoes the letterbox offset and scale (the
        window's *current* size, which can differ from ``view.window_width`` once the window is
        resized or made fullscreen), then applies the view offset (for the world renderer).
        """
        scale, dst_x, dst_y = self.display_transform()
        x, y = (x - dst_x) / scale, (y - dst_y) / scale
        if self.use_view_offset:
            x, y = x - view.offset[0], y - view.offset[1]
        return x, y

    def room_to_window(self, x: float, y: float) -> tuple[float, float]:
        """Convert a room position to a window pixel position: the inverse of ``window_to_room``."""
        if self.use_view_offset:
            x, y = x + view.offset[0], y + view.offset[1]
        scale, dst_x, dst_y = self.display_transform()
        return x * scale + dst_x, y * scale + dst_y

    def draw_display(self) -> None:
        if self._screen is None:
            return
        disp_w, disp_h = self.display.get_size()
        if disp_w == 0 or disp_h == 0:
            return
        scale, dst_x, dst_y = self.display_transform()
        if scale == 1.0:
            _ = self._screen.blit(self.display, (dst_x, dst_y))
            return
        scaled = pg.transform.scale(
            self.display, (int(disp_w * scale), int(disp_h * scale))
        )
        _ = self._screen.blit(scaled, (dst_x, dst_y))

    def fit_display(self) -> None:
        w = int(view.view_wport[view.view_current])
        h = int(view.view_hport[view.view_current])

        current: Surface | None = getattr(self, "display", None)
        if current is not None and current.get_size() == (w, h):
            current.set_clip(None)
            return

        self.display: Surface = pg.Surface((w, h))

        if self._screen is not None:
            self.display = self.display.convert()

    def fit_gui_display(self) -> None:
        """Size the GUI layer to the window and clear it, reusing the surface when possible."""
        size = (view.window_width, view.window_height)
        current: Surface | None = getattr(self, "display", None)
        if (
            current is None
            or current.get_size() != size
            or not current.get_flags() & pg.SRCALPHA
        ):
            self.display = pg.Surface(size, pg.SRCALPHA)
        self.display.set_clip(None)
        _ = self.display.fill((0, 0, 0, 0))

    def draw_set_clip(self, x: float, y: float, w: float, h: float) -> None:
        """Restrict drawing to a rectangle, until `draw_reset_clip` or the next frame."""
        x, y = self._translate_offset(x, y)
        self.display.set_clip(pg.Rect(int(x), int(y), int(w), int(h)))

    def draw_reset_clip(self) -> None:
        self.display.set_clip(None)

    def draw_surface(self, x: float, y: float, surface: pg.Surface) -> None:
        """Blit an already-prepared surface as is: the cheapest way to draw anything."""
        x, y = self._translate_offset(x, y)
        _ = self.display.blit(surface, (x, y))

    def fill_background_color(self, color: pg.Color) -> None:
        _ = self.display.fill(color)

    def set_background_images(self, surfaces: Iterable[pg.Surface]) -> None:
        self._background_images = surfaces

    def draw_background_images(self) -> None:
        for bg in self._background_images:
            _ = self.display.blit(bg, view.offset)

    def _draw_polygon(
        self,
        points: list[tuple[float, float]],
        color: pg.Color,
        outline: bool = False,
    ) -> None:
        if color.a >= 255:
            _ = pg.draw.polygon(self.display, color, points, 1 if outline else 0)
            return

        overlay = pg.Surface(self.display.get_size(), flags=pg.SRCALPHA)
        _ = pg.draw.polygon(overlay, color, points, 1 if outline else 0)
        _ = self.display.blit(overlay, (0, 0))

    def draw_circle(
        self,
        x: float,
        y: float,
        r: float,
        outline: bool = False,
        color: pg.Color | None = None,
        alpha: float = 1.0,
    ) -> None:
        """
        With this function you can draw either an outline of a circle or a filled circle. You can
        define how precise the drawing is with the function `draw_set_circle_precision()`.

        Args:
            x: The x coordinate of the center of the circle.
            y: The y coordinate of the center of the circle.
            r: The circle's radius (length from its center to its edge)
            outline: Whether the circle is drawn filled (false) or as a one pixel wide outline (true).
            color: The color to draw with. If None, uses the current draw color.
            alpha: The opacity of the circle, between 0.0 (fully transparent) and 1.0 (fully opaque).
        """
        if r <= 0:
            return

        x, y = self._translate_offset(x, y)
        draw_color = _color_with_alpha(
            self.draw_color if color is None else color, alpha
        )
        points = [
            (
                x + r * math.cos(math.tau * i / self.draw_circle_precision),
                y + r * math.sin(math.tau * i / self.draw_circle_precision),
            )
            for i in range(self.draw_circle_precision)
        ]
        self._draw_polygon(points, draw_color, outline)

    def draw_ellipse(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        outline: bool = False,
        color: pg.Color | None = None,
        alpha: float = 1.0,
    ) -> None:
        """
        With this function you can draw either an outline of an ellipse or a filled ellipse by
        defining a rectangular area that will then have the ellipse created to fit. You can define
        how precise the drawing is with the function draw_set_circle_precision().

        Args:
            x1: The x coordinate of the left of the ellipse.
            y1: The y coordinate of the top of the ellipse.
            x2: The x coordinate of the right of the ellipse.
            y2: The y coordinate of the bottom of the ellipse.
            outline: Whether the ellipse is drawn filled (false) or as a one pixel wide outline (true).
            color: The color to draw with. If None, uses the current draw color.
            alpha: The opacity of the ellipse, between 0.0 (fully transparent) and 1.0 (fully opaque).
        """
        x1, y1 = self._translate_offset(x1, y1)
        x2, y2 = self._translate_offset(x2, y2)
        radius_x = abs(x2 - x1) / 2
        radius_y = abs(y2 - y1) / 2
        if radius_x <= 0 or radius_y <= 0:
            return

        center_x = min(x1, x2) + radius_x
        center_y = min(y1, y2) + radius_y
        draw_color = _color_with_alpha(
            self.draw_color if color is None else color, alpha
        )
        points = [
            (
                center_x
                + radius_x * math.cos(math.tau * i / self.draw_circle_precision),
                center_y
                + radius_y * math.sin(math.tau * i / self.draw_circle_precision),
            )
            for i in range(self.draw_circle_precision)
        ]
        self._draw_polygon(points, draw_color, outline)

    def draw_point(
        self, x: float, y: float, color: pg.Color | None = None, alpha: float = 1.0
    ) -> None:
        x, y = self._translate_offset(x, y)
        draw_color = _color_with_alpha(
            self.draw_color if color is None else color, alpha
        )

        if alpha >= 1.0:
            _ = pg.draw.line(self.display, draw_color, (x, y), (x, y))
            return

        overlay = pg.Surface(self.display.get_size(), flags=pg.SRCALPHA)
        _ = pg.draw.line(overlay, draw_color, (x, y), (x, y))
        _ = self.display.blit(overlay, (0, 0))

    def draw_rectangle(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        outline: bool = False,
        color: pg.Color | None = None,
        alpha: float = 1.0,
    ) -> None:
        """
        This function draws either an outline of a rectangle or a filled rectangle where the (x1,y1)
        position is the top left corner and the (x2,y2) position is the bottom right corner.

        Args:
            x1: The x coordinate of the top left corner of the rectangle.
            y1: The y coordinate of the top left corner of the rectangle.
            x2: The x coordinate of the bottom right corner of the rectangle.
            y2: The y coordinate of the bottom right corner of the rectangle.
            outline: Whether the rectangle is drawn filled (false) or as a one pixel wide outline (true).
            color: The color to draw with. If None, uses the current draw color.
            alpha: The opacity of the rectangle, between 0.0 (fully transparent) and 1.0 (fully opaque).
        """
        x, y = self._translate_offset(x1, y1)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        color = _color_with_alpha(self.draw_color if color is None else color, alpha)
        rect_surf = pg.Surface((width, height), flags=pg.SRCALPHA)
        if outline:
            _ = pg.draw.rect(rect_surf, color, (0, 0, width, height), 1)
        else:
            _ = rect_surf.fill(color)
        _ = self.display.blit(rect_surf, (x, y))

    def draw_triangle(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
        col1: pg.Color | None = None,
        col2: pg.Color | None = None,
        col3: pg.Color | None = None,
        outline: bool = False,
        alpha: float = 1.0,
    ) -> None:
        """
        With this function you can draw either an outline of a triangle or a filled triangle. If it
        is filled you can define the individual colours for each corner point and if these colours
        are not the same, you will get a gradient effect from one to the other.

        Args:
            x1: The x coordinate of the triangle's first corner.
            y1: The y coordinate of the triangle's first corner.
            x2: The x coordinate of the triangle's second corner.
            y2: The y coordinate of the triangle's second corner.
            x3: The x coordinate of the triangle's third corner.
            y3: The y coordinate of the triangle's third corner.
            col1: The colour of the first corner. If None, uses the current draw color.
            col2: The colour of the second corner. If None, uses the current draw color.
            col3: The colour of the third corner. If None, uses the current draw color.
            outline: Whether the triangle is an outline (true) or filled in (false).
        """
        x1, y1 = self._translate_offset(x1, y1)
        x2, y2 = self._translate_offset(x2, y2)
        x3, y3 = self._translate_offset(x3, y3)

        col1 = _color_with_alpha(self.draw_color if col1 is None else col1, alpha)
        col2 = _color_with_alpha(self.draw_color if col2 is None else col2, alpha)
        col3 = _color_with_alpha(self.draw_color if col3 is None else col3, alpha)

        if outline:
            points = [(x1, y1), (x2, y2), (x3, y3)]
            self._draw_polygon(points, col1, outline=True)
            return

        if col1 == col2 == col3:
            self._draw_polygon([(x1, y1), (x2, y2), (x3, y3)], col1)
            return

        denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if denom == 0:
            return

        display_w, display_h = self.display.get_size()
        min_x = max(0, math.floor(min(x1, x2, x3)))
        max_x = min(display_w, math.ceil(max(x1, x2, x3)))
        min_y = max(0, math.floor(min(y1, y2, y3)))
        max_y = min(display_h, math.ceil(max(y1, y2, y3)))

        if min_x >= max_x or min_y >= max_y:
            return

        width = max_x - min_x
        height = max_y - min_y

        surf = pg.Surface((width, height), pg.SRCALPHA)

        inv_denom = 1.0 / denom

        # Barycentric value changes per screen pixel.
        w1_dx = (y2 - y3) * inv_denom
        w1_dy = (x3 - x2) * inv_denom

        w2_dx = (y3 - y1) * inv_denom
        w2_dy = (x1 - x3) * inv_denom

        # Barycentric values at the centre of the top-left pixel.
        start_x = min_x + 0.5
        start_y = min_y + 0.5

        start_w1 = ((y2 - y3) * (start_x - x3) + (x3 - x2) * (start_y - y3)) * inv_denom
        start_w2 = ((y3 - y1) * (start_x - x3) + (x1 - x3) * (start_y - y3)) * inv_denom

        c1r, c1g, c1b, c1a = col1.r, col1.g, col1.b, col1.a
        c2r, c2g, c2b, c2a = col2.r, col2.g, col2.b, col2.a
        c3r, c3g, c3b, c3a = col3.r, col3.g, col3.b, col3.a

        pixels = pg.PixelArray(surf)

        # Small tolerance avoids tiny cracks along triangle edges.
        edge_epsilon = -0.000001

        for local_y in range(height):
            w1 = start_w1 + local_y * w1_dy
            w2 = start_w2 + local_y * w2_dy

            for local_x in range(width):
                w3 = 1.0 - w1 - w2

                if w1 >= edge_epsilon and w2 >= edge_epsilon and w3 >= edge_epsilon:
                    r = int(w1 * c1r + w2 * c2r + w3 * c3r)
                    g = int(w1 * c1g + w2 * c2g + w3 * c3g)
                    b = int(w1 * c1b + w2 * c2b + w3 * c3b)
                    a = int(w1 * c1a + w2 * c2a + w3 * c3a)

                    pixels[local_x, local_y] = surf.map_rgb((r, g, b, a))  # pyright: ignore[reportIndexIssue]

                w1 += w1_dx
                w2 += w2_dx

        del pixels

        _ = self.display.blit(surf, (min_x, min_y))

    def draw_line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: pg.Color | None = None,
        alpha: float = 1.0,
    ) -> None:
        x1, y1 = self._translate_offset(x1, y1)
        x2, y2 = self._translate_offset(x2, y2)
        draw_color = _color_with_alpha(
            self.draw_color if color is None else color, alpha
        )

        if alpha >= 1.0:
            _ = pg.draw.line(self.display, draw_color, (x1, y1), (x2, y2))
            return

        overlay = pg.Surface(self.display.get_size(), flags=pg.SRCALPHA)
        _ = pg.draw.line(overlay, draw_color, (x1, y1), (x2, y2))
        _ = self.display.blit(overlay, (0, 0))

    def draw_text(
        self, x: float, y: float, string: str, color: pg.Color | None = None
    ) -> None:
        x, y = self._translate_offset(x, y)
        surface = self._render_text_with_fallback(
            string, self.draw_color if color is None else color
        )
        _ = self.display.blit(surface, (x, y))

    def text_wrap(self, string: str, max_width: float) -> list[str]:
        """Split text into the lines it takes to fit `max_width`, keeping its line breaks."""
        lines: list[str] = []
        for paragraph in string.split("\n"):
            current = ""
            for word in paragraph.split(" "):
                candidate = word if not current else f"{current} {word}"
                if current and self.text_width(candidate) > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        return lines

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
            sprite_index.x_offset
            if x_scale >= 0
            else sprite_index.width - sprite_index.x_offset
        )
        offset_y: float = (
            sprite_index.y_offset
            if y_scale >= 0
            else sprite_index.height - sprite_index.y_offset
        )

        draw_x: float = x - offset_x * scale_x_abs
        draw_y: float = y - offset_y * scale_y_abs
        draw_x, draw_y = self._translate_offset(draw_x, draw_y)

        image_index = image_index % len(sprite_index.images)
        image = sprite_index.images[image_index]

        if rotation != 0.0:
            image = pg.transform.rotate(image, rotation)

        if scale_x_abs != 1.0 or scale_y_abs != 1.0:
            image = pg.transform.scale(
                image,
                (
                    int(image.get_width() * scale_x_abs),
                    int(image.get_height() * scale_y_abs),
                ),
            )

        if x_scale < 0 or y_scale < 0:
            image = pg.transform.flip(image, x_scale < 0, y_scale < 0)

        # Sprites share their images, so anything per-draw must happen on a copy.
        if color != c_white or alpha != 1.0:
            if image is sprite_index.images[image_index]:
                image = image.copy()
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
        key = (
            self.draw_font,
            # (a font's style can be changed in place)
            (self.draw_font.bold, self.draw_font.italic, self.draw_font.underline),
            tuple(self.draw_font_fallbacks),
            string,
            (color.r, color.g, color.b, color.a),
        )
        cached = self._text_cache.get(key)
        if cached is not None:
            return cached
        if len(self._text_cache) >= _TEXT_CACHE_SIZE:
            del self._text_cache[next(iter(self._text_cache))]
        rendered = self._render_text_uncached(string, color)
        self._text_cache[key] = rendered
        return rendered

    def _render_text_uncached(self, string: str, color: pg.Color) -> pg.Surface:
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
