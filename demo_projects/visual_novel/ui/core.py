from __future__ import annotations

from typing import Protocol, Callable
from dataclasses import dataclass
import ajishio as aj
from collections.abc import Sequence

from demo_projects.visual_novel.ui.dialogue import DialogueBox


class IChoiceMenu(Protocol):
    def show(self, prompt: str, options: Sequence[ChoiceOption]) -> None: ...
    def confirm(self) -> ChoiceOption | None: ...
    def hide(self) -> None: ...


@dataclass
class ScriptContext:
    dialogue_box: DialogueBox
    choice_menu: IChoiceMenu
    set_background: Callable[[aj.Color], None]
    push_steps: Callable[[Sequence[ScriptStep]], None]


class ScriptStep(Protocol):
    def start(self, ctx: ScriptContext) -> None: ...
    def update(self, ctx: ScriptContext, dt: float) -> bool: ...


@dataclass(frozen=True)
class ChoiceOption:
    label: str
    callback: Callable[[], Sequence[ScriptStep] | None] | None = None
