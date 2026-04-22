from __future__ import annotations

from ajishio.rendering import Color
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable, override

import ajishio as aj

from demo_projects.visual_novel.ui.core import (
    ScriptContext,
    ScriptStep,
    ChoiceOption,
    IChoiceMenu,
)
from demo_projects.visual_novel.ui.dialogue import DialogueLine, DialogueBox


# =========================
# Steps
# =========================


@dataclass
class SayStep(ScriptStep):
    speaker: str
    text: str

    @override
    def start(self, ctx: ScriptContext) -> None:
        ctx.dialogue_box.show_line(DialogueLine(self.speaker, self.text))

    @override
    def update(self, ctx: ScriptContext, dt: float) -> bool:
        advance = ctx.dialogue_box.advance_requested()
        ctx.dialogue_box.update_typewriter(dt)

        if not ctx.dialogue_box.finished and advance:
            ctx.dialogue_box.reveal_all()
            return False

        if ctx.dialogue_box.finished and advance:
            ctx.dialogue_box.current_line = None
            return True

        return False


@dataclass
class ChoiceStep(ScriptStep):
    prompt: str
    options: list[ChoiceOption]

    @override
    def start(self, ctx: ScriptContext) -> None:
        ctx.choice_menu.show(self.prompt, self.options)

    @override
    def update(self, ctx: ScriptContext, dt: float) -> bool:
        confirmed = ctx.choice_menu.confirm()

        if confirmed is None:
            return False

        ctx.choice_menu.hide()
        ctx.dialogue_box.current_line = None

        if confirmed.callback is not None:
            next_steps = confirmed.callback()
            if next_steps:
                ctx.push_steps(next_steps)

        return True


@dataclass
class BackgroundStep(ScriptStep):
    color: aj.Color

    @override
    def start(self, ctx: ScriptContext) -> None:
        ctx.set_background(self.color)

    @override
    def update(self, ctx: ScriptContext, dt: float) -> bool:
        return True


@dataclass
class WaitStep(ScriptStep):
    duration: float
    remaining: float = 0.0

    @override
    def start(self, ctx: ScriptContext) -> None:
        self.remaining = self.duration

    @override
    def update(self, ctx: ScriptContext, dt: float) -> bool:
        self.remaining -= dt
        return self.remaining <= 0.0


class ScriptRunner(aj.GameObject):
    def __init__(
        self,
        steps: list[ScriptStep],
        dialogue_box: DialogueBox,
        choice_menu: IChoiceMenu,
        set_background: Callable[[aj.Color], None],
    ) -> None:
        super().__init__(0, 0)

        self._queue: deque[ScriptStep] = deque(steps)
        self.dialogue_box: DialogueBox = dialogue_box
        self.choice_menu: IChoiceMenu = choice_menu
        self.set_background: Callable[[Color], None] = set_background

        self.running: bool = True
        self.current: ScriptStep | None = None

        self.ctx: ScriptContext = ScriptContext(
            dialogue_box=dialogue_box,
            choice_menu=choice_menu,
            set_background=set_background,
            push_steps=self._push_steps,
        )

        self._start_next()

    @override
    def step(self) -> None:
        if not self.running:
            return

        if aj.keyboard_check_pressed(aj.vk_escape):
            aj.game_end()
            return

        if self.current is None:
            self.running = False
            aj.game_end()
            return

        done = self.current.update(self.ctx, aj.delta_time)

        if done:
            self._start_next()

    def _push_steps(self, steps: Sequence[ScriptStep]) -> None:
        for step in reversed(steps):
            self._queue.appendleft(step)

    def _start_next(self) -> None:
        if not self._queue:
            self.current = None
            self.running = False
            aj.game_end()
            return

        self.current = self._queue.popleft()
        self.current.start(self.ctx)
