from dataclasses import dataclass
import random
from typing import Unpack, override
import ajishio as aj
from ajishio.rendering import c_gray


@dataclass
class Shape:
    solid_map: list[list[bool]]
    color: aj.Color

    def get_rotation(self) -> list[list[bool]]:
        rotated_map = [row[:] for row in self.solid_map]
        n = len(rotated_map)
        for i in range(n):
            for j in range(i + 1, n):
                rotated_map[i][j], rotated_map[j][i] = (
                    rotated_map[j][i],
                    rotated_map[i][j],
                )
        for row in rotated_map:
            row.reverse()
        return rotated_map


# fmt: off
SHAPE_STRAIGHT = Shape([
    [False, False, False, False],
    [True,  True,  True,  True ], # Move to row 1 to rotate around center
    [False, False, False, False],
    [False, False, False, False]
], aj.c_teal)

SHAPE_SQUARE = Shape([
    [False, True,  True,  False],
    [False, True,  True,  False], 
    [False, False, False, False],
    [False, False, False, False]
], aj.c_yellow)

SHAPE_T = Shape([
    [False, True,  False, False], # Center horizontally
    [True,  True,  True,  False],
    [False, False, False, False],
    [False, False, False, False]
], aj.c_fuchsia)

SHAPE_L = Shape([
    [False, True,  False, False],
    [False, True,  False, False],
    [False, True,  True,  False], 
    [False, False, False, False]
], aj.c_orange)

SHAPE_SKEW = Shape([
    [False, True,  True,  False],
    [True,  True,  False, False],
    [False, False, False, False],
    [False, False, False, False]
], aj.c_lime)
# fmt: on


class Tile(aj.GameObject):
    DIM = 16  # Size in pixels of the tile

    def __init__(self, x: float, y: float, color: aj.Color) -> None:
        super().__init__(x, y, collision_mask=aj.CollisionMask(bbright=self.DIM, bbbottom=self.DIM))
        self.color: aj.Color = color

    @override
    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, self.DIM, self.DIM, color=self.color)

    def __repr__(self) -> str:
        return f"<Tile at ({self.x}, {self.y})>"


class Piece(aj.GameObject):
    def __init__(self, shape: Shape, x: float, y: float) -> None:
        super().__init__(x, y)
        self.shape: Shape = shape
        self.tiles: list[Tile] = self.create_tiles(self.x, self.y)

    def create_tiles(self, x: float, y: float) -> list[Tile]:
        tiles: list[Tile] = []
        for y_offset, row in enumerate(self.shape.solid_map):
            for x_offset, is_solid in enumerate(row):
                if not is_solid:
                    continue
                tiles.append(
                    Tile(
                        x + x_offset * Tile.DIM,
                        y + y_offset * Tile.DIM,
                        self.shape.color,
                    )
                )
        return tiles

    def get_xmin(self) -> float:
        leftmost = min(self.tiles, key=lambda t: t.x)
        return leftmost.x

    def get_xmax(self) -> float:
        rightmost = max(self.tiles, key=lambda t: t.x)
        return rightmost.x + Tile.DIM

    def get_ymin(self) -> float:
        top = min(self.tiles, key=lambda t: t.y)
        return top.y

    @override
    def step(self) -> None:
        super().step()
        if aj.keyboard_check_released(aj.vk_right) and self.get_xmax() < aj.room_width:
            self.move(dx=1)
        elif aj.keyboard_check_released(aj.vk_left) and self.get_xmin() > 0:
            self.move(dx=-1)

    @override
    def on_destroy(self) -> None:
        super().on_destroy()
        for tile in self.tiles:
            aj.instance_destroy(tile)

    def allowed_at_position(self, x: float, y: float, shape: Shape | None = None) -> bool:
        shape = shape or self.shape
        for y_offset, row in enumerate(shape.solid_map):
            for x_offset, is_solid in enumerate(row):
                if not is_solid:
                    continue
                tile_x = x + x_offset * Tile.DIM
                tile_y = y + y_offset * Tile.DIM
                if tile_y >= aj.room_height or tile_x < 0 or tile_x >= aj.room_width:
                    return False
                if aj.collision_rectangle(
                    tile_x, tile_y, tile_x + Tile.DIM, tile_y + Tile.DIM, Tile, set(self.tiles)
                ):
                    return False
        return True

    def move(self, dx: int = 0, dy: int = 0) -> bool:
        if not self.allowed_at_position(self.x + Tile.DIM * dx, self.y + Tile.DIM * dy):
            return False

        self.x += Tile.DIM * dx
        self.y += Tile.DIM * dy
        for tile in self.tiles:
            tile.x += Tile.DIM * dx
            tile.y += Tile.DIM * dy

        return True

    @override
    def draw(self) -> None:
        aj.draw_circle(self.x + 2 * Tile.DIM, self.y + 2 * Tile.DIM, 2, color=aj.c_red)
        for y, row in enumerate(self.shape.solid_map):
            for x, is_solid in enumerate(row):
                color = aj.c_white if is_solid else c_gray
                aj.draw_rectangle(
                    self.x + x * Tile.DIM,
                    self.y + y * Tile.DIM,
                    Tile.DIM,
                    Tile.DIM,
                    color=color,
                )


class Manager(aj.GameObject):
    BOARD_TILES_X = 12
    BOARD_TILES_Y = 24

    def __init__(self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(x, y, **kwargs)

        self.room_size: tuple[int, int] = (
            Tile.DIM * self.BOARD_TILES_X,
            Tile.DIM * self.BOARD_TILES_Y,
        )
        aj.room_set_size(*self.room_size)
        aj.window_set_size(*self.room_size)

        self.current_piece: Piece = self.spawn_piece()
        self.base_move_interval: float = 0.25
        self.set_current_move_interval()
        self.move_timer: float = self.current_move_interval

    def spawn_piece(self) -> Piece:
        shape = random.choice(
            (
                SHAPE_STRAIGHT,
                SHAPE_SQUARE,
                SHAPE_T,
                SHAPE_L,
                SHAPE_SKEW,
            )
        )
        return Piece(shape, aj.window_width / 2, Tile.DIM)

    def set_current_move_interval(self, fast: bool = False) -> None:
        self.current_move_interval = self.base_move_interval
        if fast:
            self.current_move_interval /= 4

    def check_tetris_and_destroy(self) -> bool:
        y = self.room_size[1] - Tile.DIM
        bottom_row: list[aj.IGameObject] = []
        for x in range(0, self.room_size[0], Tile.DIM):
            tile = aj.collision_rectangle(x, y, x + Tile.DIM, y + Tile.DIM, Tile)
            if tile is None:
                return False
            bottom_row.append(tile)

        for tile in bottom_row:
            aj.instance_destroy(tile)
        return True

    def shift_tiles_down(self) -> None:
        for tile in aj.instances_iterate(Tile):
            if tile not in self.current_piece.tiles:
                tile.y += Tile.DIM

    @override
    def step(self) -> None:
        super().step()
        self.move_timer -= aj.delta_time

        if aj.keyboard_check(aj.vk_down):
            self.set_current_move_interval(fast=True)
        elif aj.keyboard_check_released(aj.vk_down):
            self.set_current_move_interval()
        elif aj.keyboard_check_released(aj.vk_up) and self.current_piece.shape != SHAPE_SQUARE:
            rotated_shape = Shape(
                self.current_piece.shape.get_rotation(), self.current_piece.shape.color
            )
            if not self.current_piece.allowed_at_position(
                self.current_piece.x, self.current_piece.y, rotated_shape
            ):
                return
            piece_x, piece_y = self.current_piece.x, self.current_piece.y
            aj.instance_destroy(self.current_piece)
            self.current_piece = Piece(rotated_shape, piece_x, piece_y)

        if self.move_timer <= 0:
            self.move_timer += self.current_move_interval
            if not self.current_piece.move(dy=1):
                for tile in self.current_piece.tiles:
                    Tile(tile.x, tile.y, tile.color)
                aj.instance_destroy(self.current_piece)
                self.current_piece = self.spawn_piece()

                if self.check_tetris_and_destroy():
                    self.shift_tiles_down()


def main() -> None:
    aj.room_set_caption("Tetris")
    Manager()
    aj.game_start()


if __name__ == "__main__":
    main()
