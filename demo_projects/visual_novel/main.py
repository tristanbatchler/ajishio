from __future__ import annotations

import logging
from pathlib import Path

import ajishio as aj
from demo_projects.visual_novel.ui.choices import ChoiceMenu, ChoiceOption
from demo_projects.visual_novel.ui.dialogue import DialogueBox
from demo_projects.visual_novel.ui.script import (
    BackgroundStep,
    ChoiceStep,
    SayStep,
    ScriptRunner,
    ScriptStep,
    WaitStep,
)

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


def build_script() -> list[ScriptStep]:
    suspicion = 0

    def add_suspicion(amount: int) -> None:
        nonlocal suspicion
        suspicion += amount

    def resolve_outcome() -> list[ScriptStep]:
        if suspicion >= 2:
            return [
                SayStep(
                    "Narrator",
                    "Alarms strobe red. Security seals every exit. Mission blown.",
                ),
            ]
        if suspicion == 1:
            return [
                SayStep(
                    "Narrator",
                    "You slip through, but a patrol tags your ID. The clock starts ticking.",
                ),
            ]
        return [
            SayStep(
                "Narrator", "No eyes on you. The vault door hums open—clean entry."
            ),
        ]

    def over_explain() -> list[ScriptStep]:
        add_suspicion(1)
        return [
            SayStep(
                "You", "Absolutely, sir. The superintendent requested a dawn audit."
            ),
            SayStep("Guard", "Funny. That audit never hit my roster."),
            WaitStep(0.6),
        ] + resolve_outcome()

    def short_answer() -> list[ScriptStep]:
        return [
            SayStep("You", "Night-shift dispatch. Quick patch, then I'm gone."),
            SayStep("Guard", "Fine. Make it quick."),
            WaitStep(0.4),
        ] + resolve_outcome()

    def badge_entry() -> list[ScriptStep]:
        add_suspicion(1)
        return [
            SayStep("Narrator", "You flash a forged badge at the lobby guard."),
            ChoiceStep(
                "The guard squints at the laminate.",
                [
                    ChoiceOption(
                        "Over-explain the maintenance order", callback=over_explain
                    ),
                    ChoiceOption("Keep it short and confident", callback=short_answer),
                ],
            ),
        ]

    def tunnel_entry() -> list[ScriptStep]:
        return [
            SayStep(
                "Narrator",
                "You pry open a rusted service hatch and crawl through cables.",
            ),
            WaitStep(0.5),
        ] + resolve_outcome()

    def alarm_entry() -> list[ScriptStep]:
        return [
            SayStep(
                "Narrator",
                "You trigger a silent fire alarm. Staff scatter; cameras reroute.",
            ),
            WaitStep(0.5),
        ] + resolve_outcome()

    return [
        BackgroundStep(aj.Color(8, 10, 24)),
        SayStep("Narrator", "A midnight data heist inside Destrade Corp."),
        SayStep("Narrator", "You need the vault room before the shift change."),
        ChoiceStep(
            "How do you get inside?",
            [
                ChoiceOption(
                    "Flash a forged badge at the front desk", callback=badge_entry
                ),
                ChoiceOption("Crawl through a service tunnel", callback=tunnel_entry),
                ChoiceOption("Trigger a fire alarm distraction", callback=alarm_entry),
            ],
        ),
        BackgroundStep(aj.Color(12, 14, 32)),
        SayStep("Narrator", "Dawn bleeds through the skylights."),
        SayStep("Narrator", "Whatever you pulled tonight will echo tomorrow."),
    ]


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

ScriptRunner(build_script(), dialogue_box, choice_menu, backdrop.set_color)

aj.game_start()
