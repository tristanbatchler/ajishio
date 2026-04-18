from dataclasses import dataclass
import random
from typing import Unpack, override
import ajishio as aj


@dataclass
class Shape:
    solid_map: list[list[bool]]
    color: aj.Color


# fmt: off
SHAPE_STRAIGHT = Shape([
    [True, True, True, True],
], aj.c_teal)

SHAPE_SQUARE = Shape([
    [False, True, True],
    [False, True, True]
], aj.c_yellow)

SHAPE_T = Shape([
    [True,  True, True ],
    [False, True, False]
], aj.c_fuchsia)

SHAPE_L = Shape([
    [True, False, False],
    [True, False, False],
    [True, True,  False]
], aj.c_orange)

SHAPE_SKEW = Shape([
    [False, True,  True ],
    [True,  True,  False],
], aj.c_lime)
# fmt: on


class Tile(aj.GameObject):
    DIM: int = 16  # Size in pixels of the tile

    def __init__(self, x: float, y: float, color: aj.Color) -> None:
        super().__init__(
            x, y, collision_mask=aj.CollisionMask(bbright=self.DIM, bbbottom=self.DIM)
        )
        self.color: aj.Color = color

    @override
    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, self.DIM, self.DIM, color=self.color)

    def __repr__(self) -> str:
        return f"<Tile at ({self.x}, {self.y})>"


class Piece(aj.GameObject):
    def __init__(self, shape: Shape, x: float, y: float) -> None:
        super().__init__(x, y)
        self.tiles: list[Tile] = []
        for y_offset, row in enumerate(shape.solid_map):
            for x_offset, is_solid in enumerate(row):
                if not is_solid:
                    continue
                # This instantates all the sub-object tiles too
                self.tiles.append(
                    Tile(x + x_offset * Tile.DIM, y + y_offset * Tile.DIM, shape.color)
                )

    def get_bottom_tiles(self) -> list[Tile]:
        assert len(self.tiles) > 0, "Piece initialized with no tiles"
        bottom_val = self.tiles[0].y
        for tile in self.tiles:
            if tile.y > bottom_val:
                bottom_val = tile.y
        return [tile for tile in self.tiles if tile.y == bottom_val]

    def move_down(self) -> bool:
        bottom_tiles = self.get_bottom_tiles()
        assert len(bottom_tiles) > 0, "Piece's tiles has no bottom"
        bottom_val = bottom_tiles[0].y
        hit_bottom = bottom_val >= aj.room_height - Tile.DIM
        hit_other: aj.GameObject | None = None
        for bottom_tile in bottom_tiles:
            if hit_other := bottom_tile.place_meeting(
                bottom_tile.x, bottom_tile.y + Tile.DIM + 1, Tile
            ):
                print(f"{bottom_tile} hit {hit_other}")
        if hit_bottom or hit_other:
            return False
        for tile in self.tiles:
            tile.y += Tile.DIM
        return True


class Manager(aj.GameObject):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.current_piece: Piece | None = None
        self.move_interval: float = 0.1
        self.move_timer: float = self.move_interval

    def spawn_piece(self, shape: Shape) -> None:
        self.current_piece = Piece(shape, aj.window_width / 2, Tile.DIM)

    @override
    def step(self) -> None:
        super().step()
        self.move_timer -= aj.delta_time

        if aj.keyboard_check_released(aj.vk_space) and self.current_piece is None:
            random_shape = random.choice(
                (
                    SHAPE_STRAIGHT,
                    SHAPE_SQUARE,
                    SHAPE_T,
                    SHAPE_L,
                    SHAPE_SKEW,
                )
            )
            self.spawn_piece(random_shape)

        if self.move_timer <= 0:
            self.move_timer += self.move_interval
            if self.current_piece is not None:
                if not self.current_piece.move_down():
                    for tile in self.current_piece.tiles:
                        Tile(tile.x, tile.y, tile.color)
                    aj.instance_destroy(self.current_piece)
                    self.current_piece = None


def main() -> None:
    aj.room_set_caption("Tetris")
    Manager()
    room_size = (Tile.DIM * 20, Tile.DIM * 40)
    aj.room_set_size(*room_size)
    aj.window_set_size(*room_size)
    aj.game_start()


if __name__ == "__main__":
    main()
