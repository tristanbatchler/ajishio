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
        self.shape: Shape = shape
        self.tiles: list[Tile] = []
        self.create_tiles(self.x, self.y)

    def create_tiles(self, x: float, y: float) -> None:
        self.tiles = []
        for y_offset, row in enumerate(self.shape.solid_map):
            for x_offset, is_solid in enumerate(row):
                if not is_solid:
                    continue
                self.tiles.append(
                    Tile(
                        x + x_offset * Tile.DIM,
                        y + y_offset * Tile.DIM,
                        self.shape.color,
                    )
                )

    def get_xmin(self) -> float:
        leftmost = min(self.tiles, key=lambda t: t.x)
        return leftmost.x

    def get_xmax(self) -> float:
        rightmost = max(self.tiles, key=lambda t: t.x)
        return rightmost.x + Tile.DIM

    def get_ymin(self) -> float:
        top = min(self.tiles, key=lambda t: t.y)
        return top.y

    def get_rotation(self) -> list[list[bool]]:
        rotated_map = [row[:] for row in self.shape.solid_map]
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

    @override
    def step(self) -> None:
        super().step()
        if aj.keyboard_check_released(aj.vk_right) and self.get_xmax() < aj.room_width:
            self.move(dx=1)
        elif aj.keyboard_check_released(aj.vk_left) and self.get_xmin() > 0:
            self.move(dx=-1)

        if aj.keyboard_check_released(aj.vk_up) and self.shape != SHAPE_SQUARE:
            self.shape.solid_map = self.get_rotation()
            for tile in self.tiles:
                aj.instance_destroy(tile)
            self.create_tiles(self.get_xmin(), self.get_ymin())

    def move(self, dx: int = 0, dy: int = 0) -> bool:
        hit_other: aj.GameObject | None = None
        can_move = True
        for tile in self.tiles:
            target_x = tile.x + Tile.DIM * dx
            target_y = tile.y + Tile.DIM * dy
            if hit_other := tile.place_meeting(target_x, target_y, Tile):
                if hit_other in self.tiles:
                    continue
                print(f"{tile} hit {hit_other}")
                can_move = False
                break

            if target_y >= aj.room_height:
                print(f"{tile} hit the bottom of the room")
                can_move = False
                break

        if not can_move:
            return False

        for tile in self.tiles:
            tile.y += Tile.DIM * dy
            tile.x += Tile.DIM * dx

        return True


class Manager(aj.GameObject):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.current_piece: Piece | None = None
        self.base_move_interval: float = 0.25
        self.set_current_move_interval()
        self.move_timer: float = self.current_move_interval

    def spawn_piece(self, shape: Shape) -> None:
        self.current_piece = Piece(shape, aj.window_width / 2, Tile.DIM)

    def set_current_move_interval(self, fast: bool = False) -> None:
        self.current_move_interval = self.base_move_interval
        if fast:
            self.current_move_interval /= 4

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

        if aj.keyboard_check(aj.vk_down):
            self.set_current_move_interval(fast=True)
        elif aj.keyboard_check_released(aj.vk_down):
            self.set_current_move_interval()

        if self.move_timer <= 0:
            self.move_timer += self.current_move_interval
            if self.current_piece is not None:
                if not self.current_piece.move(dy=1):
                    aj.instance_destroy(self.current_piece)  # The tiles still exist
                    self.current_piece = None


def main() -> None:
    aj.room_set_caption("Tetris")
    Manager()
    room_size = (Tile.DIM * 12, Tile.DIM * 24)
    aj.room_set_size(*room_size)
    aj.window_set_size(*room_size)
    aj.game_start()


if __name__ == "__main__":
    main()
