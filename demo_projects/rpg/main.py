import ajishio as aj
from pathlib import Path
from enum import Enum
import math
from typing import Unpack, final, override

main_dir = Path(__file__).parent

rooms = aj.load_ldtk_levels(
    main_dir / "rooms" / "world" / "simplified",
    cosmetic_layers={"FloorIntGrid"},
)

world_pos_rooms = {
    (0, 0): 0,
    (0, 1): 1,
    (1, 0): 2,
    (2, 0): 3,
    (2, -1): 4,
}
rooms_world_pos = {room_id: world_pos for world_pos, room_id in world_pos_rooms.items()}


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
    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        # Solid tiles are spawned from CSV with width/height, usually without a sprite.
        self.collision_mask: aj.CollisionMask | None = aj.CollisionMask(
            0, 0, self.width, self.height
        )


@final
class Player(YSortObject):
    persistent = True

    def __init__(
        self, x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.sprite_index = player_sprites[PlayerSprite.SOUTH]
        self.collision_mask = aj.CollisionMask(20, 24, 28, 32)
        self.x_velocity: float = 0
        self.y_velocity: float = 0
        self.x_remainder: float = 0.0
        self.y_remainder: float = 0.0
        self.active_move_key: int | None = None
        self.move_speed: float = 70
        self.world_x: int = 0
        self.world_y: int = 0

    @override
    def step(self) -> None:
        super().step()
        movement_keys = (aj.vk_right, aj.vk_left, aj.vk_down, aj.vk_up)
        if self.active_move_key is not None and not aj.keyboard_check(
            self.active_move_key
        ):
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

        if self.collision_mask is not None:
            if self.x < -self.collision_mask.bbleft:
                self.world_move(-1, 0)
            elif self.x + self.collision_mask.bbright > aj.room_width:
                self.world_move(1, 0)
            elif self.y < -self.collision_mask.bbtop:
                self.world_move(0, -1)
            elif self.y + self.collision_mask.bbbottom > aj.room_height:
                self.world_move(0, 1)

    def world_move(self, x_offset: int, y_offset: int) -> None:
        new_world_x = self.world_x + x_offset
        new_world_y = self.world_y + y_offset
        if (new_world_x, new_world_y) not in world_pos_rooms:
            return

        self.world_x = new_world_x
        self.world_y = new_world_y
        new_room_id = world_pos_rooms[(self.world_x, self.world_y)]
        aj.room_goto(new_room_id)

        assert self.collision_mask is not None
        if x_offset == -1:
            self.x = aj.room_width - self.collision_mask.bbright - 1
        elif x_offset == 1:
            self.x = -self.collision_mask.bbleft + 1
        elif y_offset == -1:
            self.y = aj.room_height - self.collision_mask.bbbottom - 1
        elif y_offset == 1:
            self.y = -self.collision_mask.bbtop + 1

    @override
    def draw(self) -> None:
        if self.collision_mask is not None:
            aj.draw_ellipse(
                self.x + self.collision_mask.bbleft - 2,
                self.y + self.collision_mask.bbtop + 3,
                self.x + self.collision_mask.bbright + 2,
                self.y + self.collision_mask.bbbottom + 2,
                color=aj.c_black,
                alpha=0.3,
            )
        super().draw()


def main():
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
