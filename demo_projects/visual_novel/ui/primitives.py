from __future__ import annotations

import logging
from dataclasses import dataclass, field
from collections.abc import Iterable
import ajishio as aj

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PanelStyle:
    padding: float = 8.0
    bg_color: aj.Color = field(default_factory=lambda: aj.Color(12, 12, 24, 220))
    border_color: aj.Color = field(default_factory=lambda: aj.Color(64, 128, 255))
    border: bool = True


def draw_panel(x: float, y: float, w: float, h: float, style: PanelStyle) -> None:
    aj.draw_rectangle(x, y, w, h, color=style.bg_color, alpha=style.bg_color.a / 255)
    if style.border:
        aj.draw_rectangle(x, y, w, h, outline=True, color=style.border_color)


def wrap_text(text: str, max_width: float) -> list[str]:
    words: list[str] = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word]).strip()
        if candidate and aj.text_width(candidate) > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    if not lines:
        lines.append("")
    return lines


def draw_text_block(
    lines: Iterable[str],
    x: float,
    y: float,
    line_height: float,
    color: aj.Color | None = None,
) -> None:
    for i, line in enumerate(lines):
        aj.draw_text(x, y + i * line_height, line, color=color)
