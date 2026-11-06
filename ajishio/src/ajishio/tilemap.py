from __future__ import annotations

from collections.abc import Callable

import pygame as pg

import ajishio._context as _ctx
from ajishio.view import view

TileSource = Callable[[int, int, int], pg.Surface | None]


class Tilemap:
    """
    A big grid of tiles drawn cheaply: tiles are baked into chunk surfaces the first time they're
    on screen, and only the chunks in view are blitted. Thousands of tiles cost a handful of blits
    a frame, where an instance per tile would cost thousands of `step` and `draw` calls.

    The map is unbounded (tile coordinates can be negative) and is read through `source(x, y,
    frame)`, which returns the surface for a tile, or None for nothing there. With `frames` above
    1 each chunk is baked once per frame of animation and the map cycles through them, one every
    `frame_seconds`. Chunks out of view are forgotten once more than `max_cached_chunks` are baked.

    Call `draw()` from an object's `draw`, and `invalidate()` when the map changes.
    """

    def __init__(
        self,
        tile_width: int,
        tile_height: int,
        source: TileSource,
        chunk_size: int = 32,
        frames: int = 1,
        frame_seconds: float = 0.5,
        background: pg.Color | None = None,
        max_cached_chunks: int = 128,
    ) -> None:
        self.tile_width: int = tile_width
        self.tile_height: int = tile_height
        self.source: TileSource = source
        self.chunk_size: int = chunk_size
        self.frames: int = frames
        self.frame_seconds: float = frame_seconds
        self.background: pg.Color | None = background
        self.max_cached_chunks: int = max_cached_chunks
        self._chunks: dict[tuple[int, int, int], pg.Surface] = {}

    def invalidate(self) -> None:
        """Forget everything baked, because the map has changed."""
        self._chunks.clear()

    def invalidate_tile(self, x: int, y: int) -> None:
        cx, cy = x // self.chunk_size, y // self.chunk_size
        for frame in range(self.frames):
            _ = self._chunks.pop((cx, cy, frame), None)

    def _bake(self, cx: int, cy: int, frame: int) -> pg.Surface:
        size = (self.chunk_size * self.tile_width, self.chunk_size * self.tile_height)
        if self.background is not None:
            surface = pg.Surface(size).convert()
            _ = surface.fill(self.background)
        else:
            surface = pg.Surface(size, pg.SRCALPHA).convert_alpha()
        left, top = cx * self.chunk_size, cy * self.chunk_size
        blits: list[tuple[pg.Surface, tuple[int, int]]] = []
        for row in range(self.chunk_size):
            for col in range(self.chunk_size):
                tile = self.source(left + col, top + row, frame)
                if tile is not None:
                    blits.append((tile, (col * self.tile_width, row * self.tile_height)))
        _ = surface.blits(blits, doreturn=False)
        return surface

    def _current_frame(self) -> int:
        if self.frames <= 1:
            return 0
        return int(pg.time.get_ticks() / 1000 / self.frame_seconds) % self.frames

    def draw(self) -> None:
        """Draw the part of the map in the current view, from the room's origin."""
        current = view.view_current
        chunk_w = self.chunk_size * self.tile_width
        chunk_h = self.chunk_size * self.tile_height
        left = int(view.view_xport[current] // chunk_w)
        top = int(view.view_yport[current] // chunk_h)
        right = int((view.view_xport[current] + view.view_wport[current]) // chunk_w)
        bottom = int((view.view_yport[current] + view.view_hport[current]) // chunk_h)

        frame = self._current_frame()
        engine = _ctx.engine
        for cy in range(top, bottom + 1):
            for cx in range(left, right + 1):
                key = (cx, cy, frame)
                chunk = self._chunks.pop(key, None)
                if chunk is None:
                    chunk = self._bake(cx, cy, frame)
                    while len(self._chunks) >= self.max_cached_chunks:
                        del self._chunks[next(iter(self._chunks))]
                # (re-inserted last: the oldest in the dict is the longest out of view)
                self._chunks[key] = chunk
                engine.draw_surface(cx * chunk_w, cy * chunk_h, chunk)
