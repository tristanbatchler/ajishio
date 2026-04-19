from dataclasses import dataclass
from pathlib import Path
import ajishio as aj
from typing import Unpack, override


TARGET_MAX_DIMENSION = 640
MIN_CELL_SIZE = 32


@dataclass
class Difficulty:
    name: str
    width: int
    height: int
    mines: int


class Minesweeper(aj.GameObject):
    def __init__(self, difficulty: Difficulty, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(0, 0, **kwargs)
        aj.room_set_caption(f"{difficulty.name} Minesweeper")

        self.cols: int = difficulty.width
        self.rows: int = difficulty.height
        self.cell_size: int = max(
            MIN_CELL_SIZE,
            TARGET_MAX_DIMENSION // max(self.cols, self.rows),
        )

        aj.window_set_size(self.cols * self.cell_size, self.rows * self.cell_size)
        self.hovered_cell: tuple[int, int] = self.get_hovered_cell()

    def get_hovered_cell(self) -> tuple[int, int]:
        x = int(aj.mouse_x / self.cell_size)
        y = int(aj.mouse_y / self.cell_size)
        return (x, y)

    @override
    def step(self) -> None:
        super().step()
        self.hovered_cell = self.get_hovered_cell()

    @override
    def draw(self) -> None:
        super().draw()
        w = self.cols * self.cell_size
        h = self.rows * self.cell_size

        for row in range(1, self.rows):
            y = row * self.cell_size
            aj.draw_line(0, y, w, y, aj.c_gray)
        for col in range(1, self.cols):
            x = col * self.cell_size
            aj.draw_line(x, 0, x, h, aj.c_gray)

        h_x, h_y = self.hovered_cell
        aj.draw_rectangle(
            h_x * self.cell_size,
            h_y * self.cell_size,
            self.cell_size,
            self.cell_size,
            True,
            aj.c_lime,
        )


class MainMenu(aj.GameObject):
    def __init__(self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
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

    @override
    def step(self) -> None:
        super().step()
        if aj.keyboard_check_pressed(aj.vk_down):
            self.cursor_index = (self.cursor_index + 1) % len(self.difficulties)
        elif aj.keyboard_check_pressed(aj.vk_up):
            self.cursor_index = (self.cursor_index - 1) % len(self.difficulties)
        elif aj.keyboard_check_pressed(aj.vk_enter) or aj.keyboard_check_pressed(aj.vk_space):
            Minesweeper(self.difficulties[self.cursor_index])
            aj.instance_destroy(self)

    @override
    def draw(self) -> None:
        x = aj.view_xport[aj.view_current] + 20
        y_start = aj.view_yport[aj.view_current] + 20

        for i, difficulty in enumerate(self.difficulties):
            cursor = "> " if i == self.cursor_index else "  "
            option = cursor + difficulty.name

            text_height = aj.text_height(option)

            y = y_start + i * text_height * 2

            aj.draw_text(x, y, option, aj.c_yellow)


class Manager(aj.GameObject):
    def __init__(self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(x, y, **kwargs)

        MainMenu()


def main() -> None:
    aj.room_set_caption("Minesweeper")
    aj.window_set_size(400, 600)
    MainMenu()
    aj.game_start()


if __name__ == "__main__":
    main()
