import ajishio as aj
from pathlib import Path

class Floor(aj.GameObject):
    def __init__(self, x: float, y: float, tile_width: int, tile_height: int, *args, **kwargs):
        super().__init__(x, y)
        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=tile_width,
            bbbottom=tile_height
        )

    # def draw(self):
    #     # Debug outline
    #     aj.draw_rectangle(self.x, self.y, self.collision_mask.bbright, self.collision_mask.bbbottom, outline=True, color=aj.c_red)

class PhysicsObject(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y)
        self.x_velocity: float = 0
        self.y_velocity: float = 0
        self.gravity: float = 0.5

    def step(self) -> None:
        super().step()

        self.y_velocity += self.gravity

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
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y)
        self.sprite_index = sprites['player']
        self.image_speed = 10
        self.speed: float = 3.5

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
            aj.audio_play_sound(bg_music)

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

        if self.place_meeting(self.x, self.y + 1, Floor) and aj.keyboard_check(aj.vk_space):
            aj.audio_play_sound(sounds['jump'])
            self.y_velocity = self.jump_height

        if self.x < -100 or self.x > aj.room_width + 100 or self.y < -100 or self.y > aj.room_height + 100:
            aj.room_goto_next()

    def draw(self) -> None:
        super().draw()
        aj.draw_text(aj.view_xport[aj.view_current] + 10, aj.view_yport[aj.view_current] + 10, str(score), color=aj.c_yellow)

class Camera(aj.GameObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Set the display size
        aj.view_set_wport(aj.view_current, aj.room_width / 1.5)
        aj.view_set_hport(aj.view_current, aj.room_height / 1.5)

    def step(self) -> None:
        player: aj.GameObject | None = aj.instance_find(Player)
        if player is None:
            return
        
        self.x = player.x
        self.y = player.y

        half_width: float = aj.view_wport[aj.view_current] // 2
        half_height: float = aj.view_hport[aj.view_current] // 2

        self.x = aj.clamp(self.x, half_width, aj.room_width - half_width)
        self.y = aj.clamp(self.y, half_height, aj.room_height - half_height)

        aj.view_xport[aj.view_current] = self.x - half_width
        aj.view_yport[aj.view_current] = self.y - half_height

        if aj.keyboard_check(ord('r')):
            aj.room_restart()

class Enemy(PhysicsObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y)
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

        if self.place_meeting(self.x, self.y, Player):
            aj.audio_play_sound(sounds['die'])
            aj.room_restart()

class Coin(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y)
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
        if self.place_meeting(self.x, self.y, Player):
            aj.instance_destroy(self)
            global score
            score += 1
            aj.audio_play_sound(sounds['coin'])

project_dir: Path = Path(__file__).parent
sprites: dict[str, aj.GameSprite] = aj.load_aseprite_sprites(project_dir / 'sprites')
levels: list[aj.GameLevel] = aj.load_ldtk_levels(project_dir / 'room_data' / 'test' / 'simplified')
sounds: dict[str, aj.GameSound] = aj.load_sounds(project_dir / 'sounds')

aj.set_rooms(levels)
aj.register_objects(Floor, Player, Camera, Enemy, Coin)

aj.room_set_caption("Platformer")
aspect_ratio: float = levels[0].level_size[0] / levels[0].level_size[1]
aj.window_set_size(960, int(960 / aspect_ratio))

aj.room_set_background(aj.Color(135, 206, 235))

score: int = 0
aj.game_start()