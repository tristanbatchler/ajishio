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


def load_sprite_from_sheet(
    sheet_path: Path,
    width: int,
    height: int,
    padding: int = 0,
    columns: int = 1,
    rows: int = 1,
    offset_x: int = 0,
    offset_y: int = 0,
) -> GameSprite:
    images: list[pg.Surface] = []
    with open(sheet_path, "rb") as f:
        sheet = pg.image.load(f)
        for row in range(rows):
            for col in range(columns):
                x = offset_x + col * (width + padding)
                y = offset_y + row * (height + padding)
                images.append(sheet.subsurface(pg.Rect(x, y, width, height)))
    return GameSprite(images, width, height)


def sprite_set_offset(sprite: GameSprite, x_offset: float, y_offset: float) -> None:
    sprite.x_offset = x_offset
    sprite.y_offset = y_offset
