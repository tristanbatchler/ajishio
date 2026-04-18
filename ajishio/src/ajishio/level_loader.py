from collections.abc import Sequence
import csv
import json
from pathlib import Path
from typing import TypedDict, cast

import pygame as pg

from ajishio.utils import remove_ext
from ajishio.types import Entity, GameLevel

type EntitiesByType = dict[str, Sequence[Entity]]

class RawLevelInfo(TypedDict):
    width: int
    height: int
    layers: list[str]
    entities: EntitiesByType


def load_ldtk_levels(ldtk_super_simple_export_simplified_path: Path) -> list[GameLevel]:
    alphabetical_level_dirs: list[Path] = sorted(ldtk_super_simple_export_simplified_path.iterdir())
    return [load_ldtk(level_dir) for level_dir in alphabetical_level_dirs]


def load_ldtk(level_dir: Path) -> GameLevel:
    tilemaps: dict[str, list[list[bool]]] = {}
    tile_sizes: dict[str, tuple[int, int]] = {}
    background_surfaces: dict[str, pg.Surface] = {}

    level_info: RawLevelInfo = cast(
        RawLevelInfo,
        json.loads((level_dir / "data.json").read_text()),
    )

    # Get the size of this level
    level_size: tuple[int, int] = (level_info["width"], level_info["height"])

    layers: list[str] = [remove_ext(layer_filename) for layer_filename in level_info["layers"]]
    for layer in layers:
        # Get the background surface for this layer
        with open(level_dir / f"{layer}.png", "rb") as f:
            background_surfaces[layer] = pg.image.load(f)

        # Get the tilemap data for this layer
        tilemap: list[list[bool]] = []
        with open(level_dir / f"{layer}.csv", "r") as f:
            reader = csv.reader(f)
            for raw_row in reader:
                # LDTK's simplified export includes a trailing comma, so drop empty cells
                row: list[str] = [cell for cell in raw_row if cell != ""]
                tilemap.append([bool(int(cell)) for cell in row])

        # Ensure consistent row widths so placement math stays aligned
        unique_widths: set[int] = {len(r) for r in tilemap}
        if len(unique_widths) != 1:
            raise ValueError(f"Inconsistent row widths in tilemap for layer {layer}: {unique_widths}")
        tilemaps[layer] = tilemap

        # Get the tile size for this layer
        tile_size = (level_size[0] // len(tilemap[0]), level_size[1] // len(tilemap))
        tile_sizes[layer] = tile_size

    return GameLevel(tilemaps, tile_sizes, background_surfaces, level_size, level_info["entities"])
