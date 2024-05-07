import csv
import json
import pygame as pg
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from ajishio.utils import _remove_ext

@dataclass
class GameLevel:
    tilemaps: dict[str, list[list[bool]]]
    tile_sizes: dict[str, tuple[int, int]]
    background_surfaces: dict[str, pg.Surface]
    level_size: tuple[int, int]
    entities: dict[str, Any]

def load_ldtk_levels(ldtk_super_simple_export_simplified_path: Path) -> list[GameLevel]:
    alphabetical_level_dirs: list[Path] = sorted(ldtk_super_simple_export_simplified_path.iterdir())
    return [load_ldtk(level_dir) for level_dir in alphabetical_level_dirs]

def load_ldtk(level_dir: Path) -> GameLevel:
    tilemaps: dict[str, list[list[bool]]] = {}
    tile_sizes: dict[str, tuple[int, int]] = {}
    background_surfaces: dict[str, pg.Surface] = {}
    level_size: tuple[int, int]

    level_info: dict[str, Any] = json.loads((level_dir / 'data.json').read_text())
    
    # Get the size of this level
    level_size = (level_info['width'], level_info['height'])

    layers: list[str] = [_remove_ext(x) for x in level_info['layers']]
    for layer in layers:
        # Get the background surface for this layer
        with open(level_dir / f'{layer}.png', 'rb') as f:
            background_surfaces[layer] = pg.image.load(f)

        # Get the tilemap data for this layer
        tilemap: list[list[bool]] = []
        with open(level_dir / f'{layer}.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                tilemap.append([bool(int(cell)) for cell in row if cell != ''])
        tilemaps[layer] = tilemap

        # Get the tile size for this layer
        tile_size = (level_size[0] // len(tilemap[0]), level_size[1] // len(tilemap))
        tile_sizes[layer] = tile_size

    return GameLevel(tilemaps, tile_sizes, background_surfaces, level_size, level_info['entities'])

    