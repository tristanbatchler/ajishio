import inspect
import sys
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar

import pygame as pg
import math

_P = ParamSpec("_P")
_R = TypeVar("_R")


def profile(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    """Decorator that profiles *fn* when ``--profile`` is passed on the command line.

    The ``.prof`` file is saved to the current working directory and named after
    the module that owns the decorated function (e.g. ``platformer.prof``).
    Without ``--profile`` the function runs completely unmodified.

    Example::

        @aj.profile
        def main() -> None:
            aj.game_start()

        main()
    """

    @wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        if "--profile" not in sys.argv:
            return fn(*args, **kwargs)

        import cProfile
        import pstats

        # Derive a friendly name from the owning module's file path.
        module_file = inspect.getfile(fn)
        stem = Path(
            module_file
        ).parent.name  # e.g. "platformer" from .../platformer/main.py
        output_path = Path.cwd() / f"{stem}.prof"

        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return fn(*args, **kwargs)
        finally:
            profiler.disable()
            profiler.dump_stats(output_path)
            _ = pstats.Stats(profiler).sort_stats("cumulative").print_stats(30)
            print(f"\nProfile saved to {output_path.name}")
            print(f"   To visualise: uv run snakeviz {output_path.name}")

    return wrapper


def remove_ext(filename: str) -> str:
    return filename[: filename.rfind(".")]


def room_set_caption(caption: str) -> None:
    pg.display.set_caption(caption)


def lengthdir_x(length: float, direction: float) -> float:
    """
    Returns the length of the x component of a vector with the given length and direction (in radians).
    """
    return length * math.cos(direction)


def lengthdir_y(length: float, direction: float) -> float:
    """
    Returns the length of the y component of a vector with the given length and direction (in radians).
    """
    return length * math.sin(direction)


def clamp(value: float, min: float, max: float) -> float:
    return min if value < min else max if value > max else value


def map_value(
    value: float, min: float, max: float, new_min: float, new_max: float
) -> float:
    return (value - min) / (max - min) * (new_max - new_min) + new_min


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def point_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)
