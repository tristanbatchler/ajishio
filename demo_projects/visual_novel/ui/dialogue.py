from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import override

import ajishio as aj
from demo_projects.visual_novel.ui.primitives import (
    PanelStyle,
    draw_panel,
    draw_text_block,
    wrap_text,
)

_logger = logging.getLogger(__name__)


@dataclass
class DialogueLine:
    speaker: str
    text: str


class DialogueBox(aj.GameObject):
    def __init__(self, width: float) -> None:
        super().__init__(0, 0)
        self.width: float = width
        self.margin: float = 20
        self.line_height: float = 22
        self.type_rate: float = 55.0  # characters per second
        self.visible_chars: float = 0.0
        self.current_line: DialogueLine | None = None
        self.lines_wrapped: list[str] = []
        self.finished: bool = True
        self.style: PanelStyle = PanelStyle()

    def show_line(self, line: DialogueLine) -> None:
        self.current_line = line
        max_text_width = self.width - 2 * self.style.padding
        header = f"{line.speaker}:" if line.speaker else ""
        text_body = line.text
        wrapped_body = wrap_text(text_body, max_text_width)
        self.lines_wrapped = ([header] if header else []) + wrapped_body
        self.visible_chars = 0.0
        self.finished = False

    def update_typewriter(self, dt: float) -> None:
        if self.current_line is None:
            return
        if self.finished:
            return
        self.visible_chars += self.type_rate * dt
        total_length = self._total_chars()
        if self.visible_chars >= total_length:
            self.visible_chars = float(total_length)
            self.finished = True

    def advance_requested(self) -> bool:
        return aj.keyboard_check_pressed(aj.vk_space) or aj.keyboard_check_pressed(aj.vk_enter)

    def reveal_all(self) -> None:
        total_length = self._total_chars()
        self.visible_chars = float(total_length)
        self.finished = True

    def _total_chars(self) -> int:
        return sum(len(line) for line in self.lines_wrapped)

    @override
    def draw(self) -> None:
        ox = aj.view_xport[aj.view_current]
        oy = aj.view_yport[aj.view_current]

        box_w = self.width
        box_h = 140
        x = ox + self.margin
        y = oy + aj.room_height - box_h - self.margin

        draw_panel(x, y, box_w, box_h, self.style)

        if self.current_line is None:
            return

        max_chars: int = int(self.visible_chars)
        rendered_lines: list[str] = []
        remaining = max_chars
        for line in self.lines_wrapped:
            if remaining <= 0:
                break
            take = min(len(line), remaining)
            rendered_lines.append(line[:take])
            remaining -= take
        draw_text_block(
            rendered_lines,
            x + self.style.padding,
            y + self.style.padding,
            self.line_height,
        )

        if self.finished:
            prompt = "(Space/Enter to continue)"
            px = x + box_w - self.style.padding - aj.text_width(prompt)
            py = y + box_h - self.style.padding - self.line_height
            aj.draw_text(px, py, prompt, color=aj.c_ltgray)
