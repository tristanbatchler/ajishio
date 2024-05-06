import csv
import json
import pygame as pg
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class GameSprite:
    images: list[pg.Surface]
    width: int
    height: int

def load_aseprite_sprites(sprites_directory: Path) -> dict[str, GameSprite]:
    alphabetical_sprite_dirs: list[Path] = sorted(sprites_directory.iterdir())
    return {sprite_dir.name: load_aseprite_sprite(sprite_dir) for sprite_dir in alphabetical_sprite_dirs}

def load_aseprite_sprite(sprite_dir: Path) -> GameSprite:
    images: list[pg.Surface] = []
    
    png_path: Path = list(sprite_dir.glob('*.png'))[0]

    json_path: Path = list(sprite_dir.glob('*.json'))[0]
    sprite_info: dict[str, Any] = json.loads(json_path.read_text())
    frames: dict[str, Any] = sprite_info['frames']

    for data in frames.values():
        dims: dict[str, int] = data['frame']
        x, y, w, h = dims['x'], dims['y'], dims['w'], dims['h']
        with open(png_path, 'rb') as f:
            images.append(pg.image.load(f).subsurface(pg.Rect(x, y, w, h)))

    return GameSprite(images, w, h)
