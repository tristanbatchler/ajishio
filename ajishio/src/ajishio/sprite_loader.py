import json
from ajishio.types import GameSprite
from pathlib import Path
from typing import TypedDict, cast

import pygame as pg


class FrameRect(TypedDict):
    x: int
    y: int
    w: int
    h: int


class FrameData(TypedDict):
    frame: FrameRect


class SpriteInfo(TypedDict):
    frames: dict[str, FrameData]


def load_aseprite_sprites(sprites_directory: Path) -> dict[str, GameSprite]:
    alphabetical_sprite_dirs: list[Path] = sorted(sprites_directory.iterdir())
    return {
        sprite_dir.name: load_aseprite_sprite(sprite_dir) for sprite_dir in alphabetical_sprite_dirs
    }


def load_aseprite_sprite(sprite_dir: Path) -> GameSprite:
    images: list[pg.Surface] = []

    png_path: Path = next(sprite_dir.glob("*.png"))

    json_path: Path = next(sprite_dir.glob("*.json"))
    sprite_info = cast(SpriteInfo, json.loads(json_path.read_text()))
    frames: dict[str, FrameData] = sprite_info["frames"]

    sprite_width: int = 0
    sprite_height: int = 0

    for data in frames.values():
        dims: FrameRect = data["frame"]
        x, y = dims["x"], dims["y"]
        frame_width, frame_height = dims["w"], dims["h"]
        sprite_width = max(sprite_width, frame_width)
        sprite_height = max(sprite_height, frame_height)
        with open(png_path, "rb") as f:
            images.append(pg.image.load(f).subsurface(pg.Rect(x, y, frame_width, frame_height)))

    return GameSprite(images, sprite_width, sprite_height)


def sprite_set_offset(sprite: GameSprite, x_offset: float, y_offset: float) -> None:
    sprite.x_offset = x_offset
    sprite.y_offset = y_offset
