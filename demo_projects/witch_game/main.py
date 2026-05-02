from ajishio.types import GameSprite


from dataclasses import dataclass
from typing import Unpack, override
import ajishio as aj
from pathlib import Path
import enum


@dataclass
class Animation:
    name: str
    x_offset: int
    y_offset: int


class WitchGirlAnims(enum.StrEnum):
    IDLE = "idle"
    RUN = "run"
    CHARGE = "charge"
    ATTACK = "attack"
    DIE = "die"
    HURT = "hurt"


class WitchGirl(aj.GameObject):
    image_xscale: float = 1.0
    x: float

    def __init__(
        self, x: float, y: float, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)

        project_dir: Path = Path(__file__).parent
        self.sprites: dict[str, GameSprite] = aj.load_aseprite_sprites(
            project_dir / "sprites"
        )

        # Luckily this asset pack has the same offset for all animations
        SPRITE_X_OFFSET = 26
        SPRITE_Y_OFFSET = 41
        self.anims: dict[WitchGirlAnims, Animation] = {
            WitchGirlAnims.IDLE: Animation(
                "idle", x_offset=SPRITE_X_OFFSET, y_offset=SPRITE_Y_OFFSET
            ),
            WitchGirlAnims.RUN: Animation(
                "run", x_offset=SPRITE_X_OFFSET, y_offset=SPRITE_Y_OFFSET
            ),
            WitchGirlAnims.CHARGE: Animation(
                "charge", x_offset=SPRITE_X_OFFSET, y_offset=SPRITE_Y_OFFSET
            ),
            WitchGirlAnims.ATTACK: Animation(
                "attack", x_offset=SPRITE_X_OFFSET, y_offset=SPRITE_Y_OFFSET
            ),
            WitchGirlAnims.DIE: Animation(
                "die", x_offset=SPRITE_X_OFFSET, y_offset=SPRITE_Y_OFFSET
            ),
            WitchGirlAnims.HURT: Animation(
                "hurt", x_offset=SPRITE_X_OFFSET, y_offset=SPRITE_Y_OFFSET
            ),
        }

        for anim in self.anims.values():
            aj.sprite_set_offset(self.sprites[anim.name], anim.x_offset, anim.y_offset)

        self.sprite_index: aj.GameSprite | None = self.sprites[
            self.anims[WitchGirlAnims.IDLE].name
        ]

        self.image_speed: float = 10

        self.run_speed: float = 2.0

    @override
    def step(self) -> None:
        super().step()

        x_input = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)
        if x_input != 0:
            self.sprite_index = self.sprites[self.anims[WitchGirlAnims.RUN].name]
            self.image_xscale = x_input * abs(self.image_xscale)
            self.x += x_input * self.run_speed

        else:
            self.sprite_index = self.sprites[self.anims[WitchGirlAnims.IDLE].name]

        if aj.keyboard_check(ord("1")):
            self.sprite_index = self.sprites[self.anims[WitchGirlAnims.CHARGE].name]
        elif aj.keyboard_check(ord("2")):
            self.sprite_index = self.sprites[self.anims[WitchGirlAnims.ATTACK].name]
        elif aj.keyboard_check(ord("3")):
            self.sprite_index = self.sprites[self.anims[WitchGirlAnims.HURT].name]
        elif aj.keyboard_check(ord("4")):
            self.sprite_index = self.sprites[self.anims[WitchGirlAnims.DIE].name]


@aj.profile
def main() -> None:
    aj.room_set_caption("Witch Game")

    aj.room_set_size(320, 180)
    aj.window_set_size(1920, 1080)
    aj.view_set_wport(aj.view_current, aj.room_width)
    aj.view_set_hport(aj.view_current, aj.room_height)
    aj.room_set_background(aj.make_color_hsv(210, 0.5, 0.8))

    _ = WitchGirl(aj.room_width / 2, aj.room_height / 2)
    aj.game_start()


if __name__ == "__main__":
    main()
