from __future__ import annotations

import logging
from pathlib import Path

import ajishio as aj
from demo_projects.visual_novel.ui.choices import ChoiceMenu, ChoiceOption
from demo_projects.visual_novel.ui.dialogue import DialogueBox
from demo_projects.visual_novel.ui.script import BackgroundStep, ChoiceStep, SayStep, ScriptRunner, WaitStep

logger = logging.getLogger(__name__)

ROOM_WIDTH = 960
ROOM_HEIGHT = 540


class Backdrop(aj.GameObject):
    def __init__(self, color: aj.Color) -> None:
        super().__init__(0, 0)
        self.color = color

    def set_color(self, color: aj.Color) -> None:
        self.color = color

    def draw(self) -> None:
        aj.draw_rectangle(0, 0, aj.room_width, aj.room_height, color=self.color)


def build_script() -> list:
    return [
        BackgroundStep(aj.Color(10, 10, 24)),
        SayStep("Narrator", "Destrade High School's monthly meeting of first-year students."),
        SayStep("Narrator", "On the agenda: how to crush Cromartie High once and for all."),
        SayStep("Narrator", "Noboru Yamaguchi: his invincible strength has earned him the nickname the Silent Unsinkable Battleship."),
        ChoiceStep("What is Yamaguchi's nickname?", [
            ChoiceOption("The Stinking Unlikable Helicopter", next_index=6),
            ChoiceOption("The Silent Unsinkable Battleship", next_index=5),
            ChoiceOption("The Noisy Sinking Submarine", next_index=6),
        ]),
        SayStep("Narrator", "Correct! In his spare time he also leads a badass motorcycle gang named Earth, Wind, Fire."),
        SayStep("Narrator", "Incorrect. Yamaguchi is actually known as the Silent Unsinkable Battleship."),
        BackgroundStep(aj.Color(8, 8, 18)),
        WaitStep(2.0),
        SayStep("Narrator", "To be continued..."),
    ]


def main() -> None:
    aj.room_set_caption("Ajishio VN Demo")
    aj.window_set_size(ROOM_WIDTH, ROOM_HEIGHT)
    aj.room_set_size(float(ROOM_WIDTH), float(ROOM_HEIGHT))
    aj.view_set_wport(aj.view_current, aj.room_width)
    aj.view_set_hport(aj.view_current, aj.room_height)

    fonts_dir = Path(__file__).parent / "fonts"
    primary_font = aj.load_font(fonts_dir / "NotoSans-VariableFont_wdth,wght.ttf", 22)
    fallback_fonts = [
        aj.load_font(fonts_dir / "NotoSansSymbols-VariableFont_wght.ttf", 22),
        aj.load_font(fonts_dir / "NotoSansSymbols2-Regular.ttf", 22),
    ]
    aj.draw_set_font(primary_font, fallback_fonts)

    backdrop = Backdrop(aj.Color(8, 8, 18))
    dialogue_box = DialogueBox(width=aj.room_width - 40)
    choice_menu = ChoiceMenu(width=340)

    steps = build_script()
    ScriptRunner(steps, dialogue_box, choice_menu, backdrop.set_color)

    aj.game_start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
