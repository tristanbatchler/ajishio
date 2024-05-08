import ajishio as aj
from pathlib import Path
from typing import Any

class Floor(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=self.width,
            bbbottom=self.height
        )

class Doorway(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)

        self.to_room: int = self.custom_fields.get("to_room", 0)
        self.to_doorway_iid: str | None = self.custom_fields.get("to_doorway", {}).get("entityIid", None)
        
        entrance_direction_str: str = self.custom_fields["entrance_direction"]
        self.entrance_direction: tuple[int, int] = {
            "TOP": (0, -1),
            "BOTTOM": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }[entrance_direction_str]

        # Modify the collision mask to be a single pixel wide in the direction of the entrance
        self.collision_mask = aj.CollisionMask(
            bbleft=(self.width - 1) if self.entrance_direction[0] == -1 else 0,
            bbtop=(self.height - 1) if self.entrance_direction[1] == -1 else 0,
            bbright=(1 if self.entrance_direction[0] == 1 else self.width),
            bbbottom=(1 if self.entrance_direction[1] == 1 else self.height)
        )

class PhysicsObject(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.x_velocity: float = 0
        self.y_velocity: float = 0
        self.gravity: float = 0.5
        self.max_fall_speed: float = 10

    def step(self) -> None:
        super().step()

        self.y_velocity = aj.clamp(self.y_velocity + self.gravity, -self.max_fall_speed, self.max_fall_speed)

        if self.place_meeting(self.x + self.x_velocity, self.y, Floor):
            while not self.place_meeting(self.x + aj.sign(self.x_velocity), self.y, Floor):
                self.x += aj.sign(self.x_velocity)
            self.x_velocity = 0
        else:
            self.x += self.x_velocity

        if self.place_meeting(self.x, self.y + self.y_velocity, Floor):
            while not self.place_meeting(self.x, self.y + aj.sign(self.y_velocity), Floor):
                self.y += aj.sign(self.y_velocity)
            self.y_velocity = 0
        else:
            self.y += self.y_velocity
            
class Player(PhysicsObject):
    persistent: bool = True
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.sprite_index = sprites['player']
        self.image_speed = 10
        self.speed: float = 3.5
        self.score: int = 0

        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=2,
            bbleft=5,
            bbright=self.sprite_width - 5,
            bbbottom=self.sprite_height
        )

        self.jump_height: float = -8
        self.acceleration: float = 0.7

        bg_music: aj.GameSound = sounds['8_bit_ice_cave_lofi']
        if not aj.audio_is_playing(bg_music):
            aj.audio_play_sound(bg_music, loop=True)

        self.room_start_x: float = x
        self.room_start_y: float = y

    def step(self) -> None:
        super().step()
        x_input: int = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)
        
        if x_input != 0:
            self.x_velocity += x_input * self.acceleration
        else:
            self.x_velocity -= aj.sign(self.x_velocity) * self.acceleration
        
        if abs(self.x_velocity) < self.acceleration:
            self.x_velocity = 0

        self.x_velocity = aj.clamp(self.x_velocity, -self.speed, self.speed)

        if self.place_meeting(self.x, self.y + 1, Floor) and aj.keyboard_check_pressed(aj.vk_space):
            aj.audio_play_sound(sounds['jump'], gain=0.4)
            self.y_velocity = self.jump_height

        doorway_hit: aj.GameObject | None = self.place_meeting(self.x, self.y, Doorway)
        if doorway_hit and isinstance(doorway_hit, Doorway):

            entrance_dir_x, entrance_dir_y = doorway_hit.entrance_direction
            if (entrance_dir_x == 0 and entrance_dir_y == -aj.sign(self.y_velocity)) or (entrance_dir_y == 0 and entrance_dir_x == -aj.sign(self.x_velocity)):
                # We are moving in the same direction as the doorway, so we can pass through
                aj.room_goto(doorway_hit.to_room)
                
                # Move the player to the corresponding doorway on the other side
                if doorway_hit.to_doorway_iid:
                    to_doorway: aj.GameObject | None = aj.instance_find(doorway_hit.to_doorway_iid)
                    if to_doorway and isinstance(to_doorway, Doorway):

                        exit_dir_x, exit_dir_y = to_doorway.entrance_direction

                        # Take us to the corresponding position
                        player_percentage_to_bottom_doorway: float = (self.y - doorway_hit.y) / doorway_hit.height
                        player_percentage_to_right_doorway: float = (self.x - doorway_hit.x) / doorway_hit.width
                        
                        # If we are stepping through the doorway...
                        if exit_dir_x != 0:
                            self.x = to_doorway.x + exit_dir_x * to_doorway.width
                            self.y = to_doorway.y + (player_percentage_to_bottom_doorway + exit_dir_y) * to_doorway.height

                        # If we are jumping or falling through the doorway...
                        elif exit_dir_y != 0:
                            self.x = to_doorway.x + (player_percentage_to_right_doorway + exit_dir_x) * to_doorway.width
                            self.y = to_doorway.y + exit_dir_y * to_doorway.height

                        self.room_start_x = self.x
                        self.room_start_y = self.y

        if self.place_meeting(self.x, self.y, Enemy):
            aj.audio_play_sound(sounds['die'])
            aj.game_restart()

        if aj.keyboard_check_released(ord('r')):
            aj.room_restart()
            self.x = self.room_start_x
            self.y = self.room_start_y

    def draw(self) -> None:
        super().draw()
        aj.draw_text(aj.view_xport[aj.view_current] + 10, aj.view_yport[aj.view_current] + 10, str(self.score), color=aj.c_yellow)

class Camera(aj.GameObject):
    persistent: bool = True
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Set the display size
        aj.view_set_wport(aj.view_current, aj.room_width / 1.5)
        aj.view_set_hport(aj.view_current, aj.room_height / 1.5)

    def step(self) -> None:
        player: aj.GameObject | None = aj.instance_find(Player)
        if player is None:
            return
  
        self.x = aj.lerp(self.x, player.x, 0.1)
        self.y = aj.lerp(self.y, player.y, 0.1)

        half_width: float = aj.view_wport[aj.view_current] // 2
        half_height: float = aj.view_hport[aj.view_current] // 2

        self.x = aj.clamp(self.x, half_width, aj.room_width - half_width)
        self.y = aj.clamp(self.y, half_height, aj.room_height - half_height)

        aj.view_xport[aj.view_current] = self.x - half_width
        aj.view_yport[aj.view_current] = self.y - half_height

class Enemy(PhysicsObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.sprite_index = sprites['enemy']

        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=2,
            bbleft=2,
            bbright=self.sprite_width - 2,
            bbbottom=self.sprite_height
        )

        self.x_velocity = 1

    def step(self) -> None:
        super().step()

        if self.place_meeting(self.x + self.x_velocity, self.y, Floor):
            self.x_velocity *= -1

        if not self.place_meeting(self.x + self.sprite_width * aj.sign(self.x_velocity) + self.x_velocity, self.y + 1, Floor):
            self.x_velocity *= -1

class Coin(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.sprite_index = sprites['coin']

        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=self.sprite_width,
            bbbottom=self.sprite_height
        )

        self.image_speed = 15

    def step(self) -> None:
        super().step()
        player_hit: aj.GameObject | None = self.place_meeting(self.x, self.y, Player)
        if player_hit and isinstance(player_hit, Player):
            aj.instance_destroy(self)
            player_hit.score += 1
            aj.audio_play_sound(sounds['coin'])

project_dir: Path = Path(__file__).parent
sprites: dict[str, aj.GameSprite] = aj.load_aseprite_sprites(project_dir / 'sprites')
levels: list[aj.GameLevel] = aj.load_ldtk_levels(project_dir / 'room_data' / 'world' / 'simplified')
sounds: dict[str, aj.GameSound] = aj.load_sounds(project_dir / 'sounds')

aj.set_rooms(levels)
aj.register_objects(Floor, Player, Camera, Enemy, Coin, Doorway)

aj.room_set_caption("Platformer")
aspect_ratio: float = levels[0].level_size[0] / levels[0].level_size[1]
aj.window_set_size(960, int(960 / aspect_ratio))

aj.room_set_background(aj.Color(135, 206, 235))

aj.game_start()