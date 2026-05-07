import ajishio as aj
from pathlib import Path
from enum import Enum
import math
from typing import Unpack, final, override

main_dir = Path(__file__).parent


class PlayerSprite(Enum):
    """
    These are ordered in the same way as the player sprite sheet, which is important for how we
    load them.
    """

    SOUTH = 0
    NORTH = 1
    WEST = 2
    EAST = 3


def load_player_sprites() -> dict[PlayerSprite, aj.GameSprite]:
    player_sheet_path = main_dir / "sprites" / "player.png"

    player_sprites: dict[PlayerSprite, aj.GameSprite] = {}

    for i, direction in enumerate(PlayerSprite):
        player_sprites[direction] = aj.load_sprite_from_sheet(
            player_sheet_path,
            width=48,
            height=48,
            columns=4,
            offset_y=i * 48,
        )

    return player_sprites


player_sprites = load_player_sprites()


class YSortObject(aj.GameObject):
    @override
    def step(self) -> None:
        super().step()
        self.depth = -int(self.y)  # pyright: ignore[reportUnannotatedClassAttribute]
        # TODO: This doesn't work for walls because they are painted into the background, not real
        # objects.


class Solid(YSortObject):
    def __init__(self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(x, y, **kwargs)
        # Solid tiles are spawned from CSV with width/height, usually without a sprite.
        self.collision_mask: aj.CollisionMask | None = aj.CollisionMask(
            0, 0, self.width, self.height
        )

    @override
    def draw(self) -> None:
        super().draw()
        if self.collision_mask is not None:
            x = self.x + self.collision_mask.bbleft
            y = self.y + self.collision_mask.bbtop
            w = self.collision_mask.bbright - self.collision_mask.bbleft
            h = self.collision_mask.bbbottom - self.collision_mask.bbtop

            aj.draw_rectangle(x, y, w, h, color=aj.c_red, alpha=0.5)


@final
class Player(YSortObject):
    def __init__(self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(x, y, **kwargs)
        self.sprite_index = player_sprites[PlayerSprite.SOUTH]
        self.collision_mask = aj.CollisionMask(20, 24, 28, 32)
        self.x_velocity: float = 0
        self.y_velocity: float = 0
        self.x_remainder = 0.0
        self.y_remainder = 0.0
        self.active_move_key: int | None = None
        self.move_speed = 70

    @override
    def step(self) -> None:
        super().step()
        movement_keys = (aj.vk_right, aj.vk_left, aj.vk_down, aj.vk_up)
        if self.active_move_key is not None and not aj.keyboard_check(self.active_move_key):
            self.active_move_key = None
            self.image_index = 0

        if self.active_move_key is None:
            for key in movement_keys:
                if aj.keyboard_check_pressed(key):
                    self.active_move_key = key
                    break

                if aj.keyboard_check(key):
                    self.active_move_key = key
                    break

        x_input = 0
        y_input = 0
        match self.active_move_key:
            case aj.vk_right:
                x_input = 1
                self.sprite_index = player_sprites[PlayerSprite.EAST]
            case aj.vk_left:
                x_input = -1
                self.sprite_index = player_sprites[PlayerSprite.WEST]
            case aj.vk_down:
                y_input = 1
                self.sprite_index = player_sprites[PlayerSprite.SOUTH]
            case aj.vk_up:
                y_input = -1
                self.sprite_index = player_sprites[PlayerSprite.NORTH]
            case _:
                pass

        self.image_speed = 0 if x_input == 0 and y_input == 0 else 10

        self.x_velocity = x_input * self.move_speed
        self.y_velocity = y_input * self.move_speed

        # Move in integer pixels for stable collision boundaries, while preserving
        # fractional speed via remainders.
        self.x_remainder += self.x_velocity * aj.delta_time
        self.y_remainder += self.y_velocity * aj.delta_time

        x_move = math.trunc(self.x_remainder)
        y_move = math.trunc(self.y_remainder)
        self.x_remainder -= x_move
        self.y_remainder -= y_move

        x_step = aj.sign(x_move)
        for _ in range(abs(x_move)):
            next_x = self.x + x_step
            if self.place_meeting(next_x, self.y, Solid):
                self.x_remainder = 0.0
                break
            self.x = next_x

        y_step = aj.sign(y_move)
        for _ in range(abs(y_move)):
            next_y = self.y + y_step
            if self.place_meeting(self.x, next_y, Solid):
                self.y_remainder = 0.0
                break
            self.y = next_y

    @override
    def draw(self) -> None:
        super().draw()
        if self.collision_mask is not None:
            x = self.x + self.collision_mask.bbleft
            y = self.y + self.collision_mask.bbtop
            w = self.collision_mask.bbright - self.collision_mask.bbleft
            h = self.collision_mask.bbbottom - self.collision_mask.bbtop

            aj.draw_rectangle(x, y, w, h, color=aj.c_lime, alpha=0.5)


def main():
    rooms = aj.load_ldtk_levels(
        main_dir / "rooms" / "world" / "simplified",
        cosmetic_layers={"FloorIntGrid"},
    )

    aj.set_rooms(rooms)
    w = int(aj.room_width)
    h = int(aj.room_height)
    aj.window_set_size(w * 4, h * 4)
    aj.view_set_wport(aj.view_current, w)
    aj.view_set_hport(aj.view_current, h)
    aj.room_set_caption("RPG")
    aj.register_objects(Player, Solid)

    aj.game_start()


if __name__ == "__main__":
    main()
