import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

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


@dataclass
class GameSprite:
    images: list[pg.Surface]
    width: int
    height: int


def load_aseprite_sprites(sprites_directory: Path) -> dict[str, GameSprite]:
    alphabetical_sprite_dirs: list[Path] = sorted(sprites_directory.iterdir())
    return {
        sprite_dir.name: load_aseprite_sprite(sprite_dir) for sprite_dir in alphabetical_sprite_dirs
    }


def load_aseprite_sprite(sprite_dir: Path) -> GameSprite:
    images: list[pg.Surface] = []

    png_path: Path = next(sprite_dir.glob("*.png"))

    json_path: Path = next(sprite_dir.glob("*.json"))
    sprite_info: SpriteInfo = json.loads(json_path.read_text())
    frames: dict[str, FrameData] = sprite_info["frames"]

    width: int = 0
    height: int = 0

    for data in frames.values():
        dims: FrameRect = data["frame"]
        x, y, width, height = dims["x"], dims["y"], dims["w"], dims["h"]
        with open(png_path, "rb") as f:
            images.append(pg.image.load(f).subsurface(pg.Rect(x, y, width, height)))

    return GameSprite(images, width, height)
