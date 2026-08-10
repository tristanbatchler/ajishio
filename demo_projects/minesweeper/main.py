from ajishio.types import GameSprite


from dataclasses import dataclass
from enum import IntEnum, auto
from pathlib import Path
from random import randrange
from collections.abc import Iterable
from typing import Unpack, override

import ajishio as aj


TARGET_MAX_DIMENSION = 640
MIN_CELL_SIZE = 32


@dataclass
class Difficulty:
    name: str
    width: int
    height: int
    mines: int


@dataclass
class Cell:
    has_mine: bool
    flagged: bool
    adjacent_mines: int
    revealed: bool


class Minesweeper(aj.GameObject):
    class SpriteIndices(IntEnum):
        NUMBER_0 = 0
        NUMBER_1 = auto()
        NUMBER_2 = auto()
        NUMBER_3 = auto()
        NUMBER_4 = auto()
        NUMBER_5 = auto()
        NUMBER_6 = auto()
        NUMBER_7 = auto()
        NUMBER_8 = auto()
        UNKNOWN = auto()
        FLAG = auto()
        QUESTION_UP = auto()
        QUESTION_DOWN = auto()
        MINE = auto()
        EXPLODED_MINE = auto()

    sprite_sheet: GameSprite = aj.load_aseprite_sprite(
        Path(__file__).parent / "sprites"
    )

    def __init__(
        self, difficulty: Difficulty, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(0, 0, **kwargs)
        aj.room_set_caption(f"{difficulty.name} Minesweeper")
        self.num_mines: int = difficulty.mines
        self.cols: int = difficulty.width
        self.rows: int = difficulty.height
        self.cell_size: int = max(
            MIN_CELL_SIZE,
            TARGET_MAX_DIMENSION // max(self.cols, self.rows),
        )

        aj.window_set_size(self.cols * self.cell_size, self.rows * self.cell_size)
        self.hovered_cell: tuple[int, int] = self.get_hovered_cell()

        self.grid: dict[tuple[int, int], Cell] = {}
        for x in range(self.cols):
            for y in range(self.rows):
                self.grid[(x, y)] = Cell(
                    has_mine=False,
                    revealed=False,
                    flagged=False,
                    adjacent_mines=0,
                )

        self.game_over: bool = False

        self.mines_locations: set[tuple[int, int]] = set()

    def place_mines(self, avoid: tuple[int, int]) -> None:
        placed = 0
        while placed < self.num_mines:
            x = randrange(0, self.cols)
            y = randrange(0, self.rows)
            if (x, y) == avoid:
                continue
            cell = self.grid[(x, y)]
            if not cell.has_mine:
                cell.has_mine = True
                self.mines_locations.add((x, y))
                placed += 1

        self.update_neighbors()

    def get_neighbour_locations(self, x: int, y: int) -> Iterable[tuple[int, int]]:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == dy == 0:
                    continue
                n_x = x + dx
                n_y = y + dy
                if (n_x, n_y) in self.grid:
                    yield (n_x, n_y)

    def update_neighbors(self) -> None:
        for x, y in self.mines_locations:
            for neighbor in self.get_neighbour_locations(x, y):
                self.grid[neighbor].adjacent_mines += 1

    def get_hovered_cell(self) -> tuple[int, int]:
        x = int(aj.mouse_x / self.cell_size)
        y = int(aj.mouse_y / self.cell_size)
        return (x, y)

    @override
    def step(self) -> None:
        super().step()
        self.hovered_cell = self.get_hovered_cell()

        if self.game_over:
            continue_keys = (aj.vk_enter, aj.vk_space, aj.vk_escape)
            if any(aj.keyboard_check_pressed(key) for key in continue_keys):
                _ = MainMenu()
                aj.instance_destroy(self)
            return

        if aj.mouse_check_button_released(aj.mb_left):
            if len(self.mines_locations) == 0:
                self.place_mines(self.hovered_cell)
            self.reveal_cell(self.hovered_cell)
        elif aj.mouse_check_button_released(aj.mb_right):
            self.toggle_flag(self.hovered_cell)

    def reveal_cell(self, location: tuple[int, int]) -> None:
        cell = self.grid[location]

        if cell.revealed or cell.flagged:
            return

        cell.revealed = True
        if cell.has_mine:
            self.run_game_over_sequence()
            return

        self.check_win()

        if cell.adjacent_mines == 0:
            self.flood_fill(*location)

    def run_game_over_sequence(self) -> None:
        aj.room_set_caption("Game Over!")
        self.game_over = True
        for location in self.mines_locations:
            self.grid[location].revealed = True

    def toggle_flag(self, location: tuple[int, int]) -> None:
        cell = self.grid[location]

        if cell.revealed:
            return

        cell.flagged = not cell.flagged
        self.check_win()

    def check_win(self) -> None:
        # Win if all non-mine cells are revealed and all mines are flagged
        all_cells = self.grid.values()
        won = all(
            (cell.has_mine and cell.flagged) or (not cell.has_mine and cell.revealed)
            for cell in all_cells
        )
        if won:
            aj.room_set_caption("You win!")
            self.game_over = True

    def flood_fill(self, x: int, y: int) -> None:
        for n_x, n_y in self.get_neighbour_locations(x, y):
            neighbor = self.grid[(n_x, n_y)]
            if not neighbor.revealed and not neighbor.has_mine:
                neighbor.revealed = True
                if neighbor.adjacent_mines == 0:
                    self.flood_fill(n_x, n_y)

    @override
    def draw(self) -> None:
        super().draw()

        for (x, y), cell in self.grid.items():
            subimg = self.SpriteIndices.UNKNOWN
            if cell.revealed:
                if cell.has_mine:
                    subimg = self.SpriteIndices.EXPLODED_MINE
                else:
                    # We can do this because we strategically front-loaded the sprite sheet with
                    # the number sprites in order
                    subimg = cell.adjacent_mines
            elif cell.flagged:
                subimg = self.SpriteIndices.FLAG
            aj.draw_sprite(
                x * self.cell_size,
                y * self.cell_size,
                self.sprite_sheet,
                subimg,
                x_scale=self.cell_size / self.sprite_sheet.width,
                y_scale=self.cell_size / self.sprite_sheet.height,
            )

        h_x, h_y = self.hovered_cell
        x = h_x * self.cell_size
        y = h_y * self.cell_size
        aj.draw_rectangle(
            x1=x,
            y1=y,
            x2=+self.cell_size,
            y2=y + self.cell_size,
            outline=True,
            color=aj.c_lime,
        )


class MainMenu(aj.GameObject):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)

        self.difficulties: list[Difficulty] = [
            Difficulty("Beginner", 8, 8, 10),
            Difficulty("Intermediate", 16, 16, 40),
            Difficulty("Expert", 30, 16, 99),
        ]

        self.cursor_index: int = 0
        font_path = (Path(__file__).parent / "AdwaitaMono-Regular.ttf").resolve()
        font = aj.load_font(font_path, 24)
        aj.draw_set_font(font)

        self.difficulties_y1_y2: list[tuple[float, float]] = []
        for i, difficulty in enumerate(self.difficulties):
            option = difficulty.name
            text_height = aj.text_height(option)
            y_start = aj.view_yport[aj.view_current] + 20
            y = y_start + i * text_height * 2
            self.difficulties_y1_y2.append((y, y + text_height))

    @override
    def step(self) -> None:
        super().step()
        if aj.keyboard_check_pressed(aj.vk_down):
            self.cursor_index = (self.cursor_index + 1) % len(self.difficulties)
        elif aj.keyboard_check_pressed(aj.vk_up):
            self.cursor_index = (self.cursor_index - 1) % len(self.difficulties)
        elif (
            aj.keyboard_check_pressed(aj.vk_enter)
            or aj.keyboard_check_pressed(aj.vk_space)
            or aj.mouse_check_button_released(aj.mb_left)
        ):
            _ = Minesweeper(self.difficulties[self.cursor_index])
            aj.instance_destroy(self)

        for i, (y1, y2) in enumerate(self.difficulties_y1_y2):
            if aj.mouse_y >= y1 and aj.mouse_y <= y2:
                self.cursor_index = i

    @override
    def draw(self) -> None:
        x = aj.view_xport[aj.view_current] + 20

        for difficulty, (y1, _) in zip(
            self.difficulties, self.difficulties_y1_y2, strict=False
        ):
            prefix, color = "  ", aj.c_white
            if self.difficulties[self.cursor_index] == difficulty:
                prefix, color = "> ", aj.c_lime

            entry = prefix + difficulty.name
            aj.draw_text(x, y1, entry, color)


class Manager(aj.GameObject):
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)

        _ = MainMenu()


aj.room_set_caption("Minesweeper")
aj.window_set_size(400, 600)
_ = MainMenu()
aj.game_start()
