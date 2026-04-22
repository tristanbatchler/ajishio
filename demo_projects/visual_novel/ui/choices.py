from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

import ajishio as aj

from demo_projects.visual_novel.ui.core import ChoiceOption
from demo_projects.visual_novel.ui.primitives import (
    PanelStyle,
    draw_panel,
    draw_text_block,
)

_logger = logging.getLogger(__name__)


class ChoiceMenu(aj.GameObject):
    def __init__(self, width: float) -> None:
        super().__init__(0, 0)

        self.width: float = width
        self.margin: float = 20
        self.line_height: float = 22

        self.options: list[ChoiceOption] = []
        self.prompt: str | None = None
        self.selected: int = 0
        self.visible: bool = False

        self.style: PanelStyle = PanelStyle(
            bg_color=aj.Color(16, 16, 32, 230),
            border_color=aj.Color(180, 200, 255),
        )

        self._arrow_glyph: str = "➤"

    def show(self, prompt: str, options: Sequence[ChoiceOption]) -> None:
        self.prompt = prompt
        self.options = list(options)  # normalize
        self.selected = 0
        self.visible = True

    def hide(self) -> None:
        self.visible = False
        self.prompt = None
        self.options = []

    @override
    def step(self) -> None:
        if not self.visible:
            return

        if aj.keyboard_check_pressed(aj.vk_down):
            self.selected = (self.selected + 1) % len(self.options)

        elif aj.keyboard_check_pressed(aj.vk_up):
            self.selected = (self.selected - 1) % len(self.options)

    def confirm(self) -> ChoiceOption | None:
        if not self.visible:
            return None

        if aj.keyboard_check_pressed(aj.vk_enter) or aj.keyboard_check_pressed(aj.vk_space):
            return self.options[self.selected]

        return None

    @override
    def draw(self) -> None:
        if not self.visible:
            return

        ox = aj.view_xport[aj.view_current]
        oy = aj.view_yport[aj.view_current]

        box_w = self.width
        prompt_h = self.line_height if self.prompt else 0

        box_h = (
            prompt_h
            + len(self.options) * self.line_height
            + 20
            + (self.style.padding if self.prompt else 0)
        )

        x = ox + aj.room_width - box_w - self.margin
        y = oy + self.margin

        draw_panel(x, y, box_w, box_h, self.style)

        text_y = y + self.style.padding

        if self.prompt:
            aj.draw_text(
                x + self.style.padding,
                text_y,
                self.prompt,
                color=aj.c_ltgray,
            )
            text_y += self.line_height + self.style.padding

        arrow_w = aj.text_width(self._arrow_glyph)
        arrow_h = aj.text_height(self._arrow_glyph)
        arrow_slot = max(arrow_w, int(self.line_height * 0.6))

        arrow_x = x + self.style.padding
        text_x = arrow_x + arrow_slot + 6

        labels: list[str] = []

        for i, opt in enumerate(self.options):
            labels.append(opt.label)

            if i == self.selected:
                ay = text_y + i * self.line_height + (self.line_height - arrow_h) / 2
                aj.draw_text(arrow_x, ay, self._arrow_glyph, color=aj.c_white)

        draw_text_block(labels, text_x, text_y, self.line_height, color=aj.c_white)
