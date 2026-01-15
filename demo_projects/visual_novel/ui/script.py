from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

import ajishio as aj
from demo_projects.visual_novel.ui.choices import ChoiceMenu, ChoiceOption
from demo_projects.visual_novel.ui.dialogue import DialogueBox, DialogueLine

_logger = logging.getLogger(__name__)

@dataclass
class ScriptStep:
    pass


@dataclass
class SayStep(ScriptStep):
    speaker: str
    text: str


@dataclass
class ChoiceStep(ScriptStep):
    prompt: str
    options: list[ChoiceOption]


@dataclass
class BackgroundStep(ScriptStep):
    color: aj.Color


@dataclass
class WaitStep(ScriptStep):
    duration: float


class ScriptRunner(aj.GameObject):
    def __init__(
        self,
        steps: list[ScriptStep],
        dialogue_box: DialogueBox,
        choice_menu: ChoiceMenu,
        set_background: Callable[[aj.Color], None],
    ) -> None:
        super().__init__(0, 0)
        self.steps = steps
        self.dialogue_box = dialogue_box
        self.choice_menu = choice_menu
        self.set_background = set_background
        self.index: int = 0
        self.wait_timer: float = 0.0
        self.running: bool = True

    def step(self) -> None:
        if not self.running:
            return
        if aj.keyboard_check_pressed(aj.vk_escape):
            aj.game_end()
            return
        if self.index >= len(self.steps):
            self.running = False
            aj.game_end()
            return

        current = self.steps[self.index]
        match current:
            case BackgroundStep(color=color):
                self.set_background(color)
                self.index += 1
            case WaitStep(duration=duration):
                self.wait_timer += aj.delta_time
                if self.wait_timer >= duration:
                    self.wait_timer = 0.0
                    self.index += 1
            case SayStep(speaker=speaker, text=text):
                if self.dialogue_box.current_line is None:
                    self.dialogue_box.show_line(DialogueLine(speaker, text))
                    return
                self.dialogue_box.update_typewriter(aj.delta_time)
                if self.dialogue_box.finished and self.dialogue_box.advance_requested():
                    self.dialogue_box.current_line = None
                    self.index += 1
            case ChoiceStep(options=options):
                if not self.choice_menu.visible:
                    self.choice_menu.show(current.prompt, options)
                confirmed = self.choice_menu.confirm()
                if confirmed is not None:
                    self.choice_menu.hide()
                    self.dialogue_box.current_line = None
                    self.index = confirmed.next_index
            case _:
                _logger.warning("Unknown script step type: %s", type(current).__name__)
                self.index += 1
