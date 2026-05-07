from dataclasses import dataclass
import random
from typing import Literal, Unpack, override
import ajishio as aj

type SolidMap = list[list[Literal[0, 1]]]


@dataclass
class Shape:
    solid_map: SolidMap
    color: aj.Color

    def get_rotation(self) -> SolidMap:
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


SHAPE_STRAIGHT = Shape(
    [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    aj.c_teal,
)

SHAPE_SQUARE = Shape(
    [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ],
    aj.c_yellow,
)

SHAPE_T = Shape(
    [
        [0, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
    ],
    aj.c_fuchsia,
)

SHAPE_L = Shape(
    [
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ],
    aj.c_orange,
)

SHAPE_SKEW = Shape(
    [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 0],
    ],
    aj.c_lime,
)


class Tile(aj.GameObject):
    DIM: int = 16  # Size in pixels of the tile

    def __init__(self, x: float, y: float, color: aj.Color) -> None:
        super().__init__(x, y, collision_mask=aj.CollisionMask(bbright=self.DIM, bbbottom=self.DIM))
        self.color: aj.Color = color

    @override
    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, self.x + self.DIM, self.y + self.DIM, color=self.color)

    @override
    def __repr__(self) -> str:
        return f"<Tile at ({self.x}, {self.y})>"


class Piece(aj.GameObject):
    x: float
    y: float

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
        if (
            aj.keyboard_check_released(aj.vk_right)
            and self.get_xmax() < aj.view_wport[aj.view_current]
        ):
            _ = self.move(dx=1)
        elif aj.keyboard_check_released(aj.vk_left) and self.get_xmin() > 0:
            _ = self.move(dx=-1)

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
                if (
                    tile_y >= aj.view_hport[aj.view_current]
                    or tile_x < 0
                    or tile_x >= aj.view_wport[aj.view_current]
                ):
                    return False
                if aj.collision_rectangle(
                    tile_x,
                    tile_y,
                    tile_x + Tile.DIM,
                    tile_y + Tile.DIM,
                    Tile,
                    self.tiles,
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

    def apply_shape(self, shape: Shape, x: float, y: float) -> None:
        self.shape = shape
        self.x = x
        self.y = y

        target_positions: list[tuple[float, float]] = []
        for y_offset, row in enumerate(shape.solid_map):
            for x_offset, is_solid in enumerate(row):
                if not is_solid:
                    continue
                target_positions.append((x + x_offset * Tile.DIM, y + y_offset * Tile.DIM))

        # All current tetromino definitions use 4 solid cells.
        if len(target_positions) != len(self.tiles):
            return

        for tile, (tile_x, tile_y) in zip(self.tiles, target_positions):
            tile.x = tile_x
            tile.y = tile_y


class Manager(aj.GameObject):
    current_move_interval: float

    def __init__(self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(x, y, **kwargs)

        self.current_piece: Piece | None = self.spawn_piece()
        self.base_move_interval: float = 0.25
        self.set_current_move_interval()
        self.move_timer: float = self.current_move_interval
        self.game_over: bool = False
        self.score: int = 0
        self.depth: int = -999

    def spawn_piece(self) -> Piece | None:
        shape = random.choice(
            (
                SHAPE_STRAIGHT,
                SHAPE_SQUARE,
                SHAPE_T,
                SHAPE_L,
                SHAPE_SKEW,
            )
        )
        shape_width = len(shape.solid_map[0]) * Tile.DIM
        new_piece = Piece(shape, (aj.room_width - shape_width) / 2, Tile.DIM)
        if not new_piece.allowed_at_position(new_piece.x, new_piece.y):
            aj.instance_destroy(new_piece)
            return None
        return new_piece

    def set_current_move_interval(self, fast: bool = False) -> None:
        self.current_move_interval = self.base_move_interval
        if fast:
            self.current_move_interval /= 4

    def shift_tiles_above(self, y: float) -> None:
        if self.current_piece is None:
            return
        for tile in aj.instances_iterate(Tile):
            if tile.y < y and tile not in self.current_piece.tiles:
                tile.y += Tile.DIM

    def clear_full_rows(self) -> None:
        y = aj.view_hport[aj.view_current] - Tile.DIM
        while y >= 0:
            row_tiles: list[aj.IGameObject] = []
            is_full = True

            for x in range(0, int(aj.view_wport[aj.view_current]), Tile.DIM):
                tile = aj.instance_position(x + Tile.DIM // 2, y + Tile.DIM // 2, Tile)
                if tile is None:
                    is_full = False
                    break
                row_tiles.append(tile)

            if not is_full:
                y -= Tile.DIM
                continue

            self.shift_tiles_above(y)
            for tile in row_tiles:
                self.score += 10
                aj.instance_destroy(tile)
            # Re-check same y because a dropped row may also be full.

    @override
    def step(self) -> None:
        super().step()
        self.move_timer -= aj.delta_time

        if self.current_piece is None:
            self.game_over = True
            return

        if aj.keyboard_check_released(ord("r")):
            aj.game_restart()
            _ = Manager()
        elif aj.keyboard_check(aj.vk_down):
            self.set_current_move_interval(fast=True)
        elif aj.keyboard_check_released(aj.vk_down):
            self.set_current_move_interval()
        elif aj.keyboard_check_released(aj.vk_up) and self.current_piece.shape != SHAPE_SQUARE:
            rotated_shape = Shape(
                self.current_piece.shape.get_rotation(), self.current_piece.shape.color
            )
            # Try wall kicks: attempt offsets in order until one fits
            kick_offsets = [0, -1, 1, -2, 2]
            kicked_x: float | None = None
            for offset in kick_offsets:
                test_x = self.current_piece.x + offset * Tile.DIM
                if self.current_piece.allowed_at_position(
                    test_x, self.current_piece.y, rotated_shape
                ):
                    kicked_x = test_x
                    break
            if kicked_x is None:
                pass  # No valid position found, don't rotate
            else:
                self.current_piece.apply_shape(rotated_shape, kicked_x, self.current_piece.y)

        if self.move_timer <= 0:
            self.move_timer += self.current_move_interval
            if not self.current_piece.move(dy=1):
                for tile in self.current_piece.tiles:
                    _ = Tile(tile.x, tile.y, tile.color)
                aj.instance_destroy(self.current_piece)
                self.clear_full_rows()
                self.current_piece = self.spawn_piece()

    @override
    def draw(self) -> None:
        super().draw()
        if self.game_over:
            message = "GAME OVER"
            msg_width = aj.text_width(message)
            msg_height = aj.text_height(message)
            x = (aj.view_wport[aj.view_current] - msg_width) / 2
            y = (aj.view_hport[aj.view_current] - msg_height) / 2
            aj.draw_text(x, y, message, aj.c_red)

            score_text = f"Your score: {self.score}"
            score_width = aj.text_width(score_text)
            score_x = (aj.view_wport[aj.view_current] - score_width) / 2
            score_y = y + msg_height + 10
            aj.draw_text(score_x, score_y, score_text, aj.c_white)
        else:
            score_text = f"SCORE: {self.score}"
            aj.draw_text(
                aj.view_xport[aj.view_current] + 10,
                aj.view_yport[aj.view_current] + 10,
                score_text,
                aj.c_white,
            )


aj.room_set_caption("Tetris")
size = (10 * Tile.DIM, 20 * Tile.DIM)
aj.room_set_size(*size)
aj.window_set_size(size[0] * 2, size[1] * 2)
aj.view_set_wport(aj.view_current, size[0])
aj.view_set_hport(aj.view_current, size[1])
_ = Manager()
aj.game_start()
