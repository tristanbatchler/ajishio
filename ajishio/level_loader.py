import csv
import json
import pygame as pg
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class GameLevel:
    tilemap: list[list[bool]]
    tile_size: tuple[int, int]
    level_size: tuple[int, int]
    background_surface: pg.Surface
    entities: dict[str, Any]

def load_ldtk(level_dir: Path) -> GameLevel:
    tilemap: list[list[bool]] = []
    tile_size: tuple[int, int]
    level_size: tuple[int, int]
    background_surface: pg.Surface

    with open(level_dir / 'GroundIntLayer.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            tilemap.append([bool(int(cell)) for cell in row if cell != ''])

    level_info: dict[str, Any] = json.loads((level_dir / 'data.json').read_text())
    level_size = (level_info['width'], level_info['height'])
    tile_size = (level_size[0] // len(tilemap[0]), level_size[1] // len(tilemap))

    with open(level_dir / '_composite.png', 'rb') as f:
        background_surface = pg.image.load(f)

    return GameLevel(tilemap, tile_size, level_size, background_surface, level_info['entities'])

    