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

class Player(aj.GameObject):
    def __init__(self, x: float, y: float, *args, width: float = 16, height: float = 32, speed: float = 5, **kwargs):
        super().__init__(x, y)
        self.width: float = width
        self.height: float = height
        self.speed: float = speed

        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=width,
            bbbottom=height
        )

        self.x_velocity: float = 0
        self.y_velocity: float = 0
        self.gravity: float = 0.5
        self.jump_height: float = -8.5

    def step(self) -> None:
        x_input: int = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)
        
        self.x_velocity = x_input * self.speed
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

        if self.place_meeting(self.x, self.y + 1, Floor) and aj.keyboard_check(aj.vk_space):
            self.y_velocity = self.jump_height

        if self.x < -100 or self.x > aj.room_width + 100 or self.y < -100 or self.y > aj.room_height + 100:
            aj.room_goto_next()

    def draw(self):
        aj.draw_rectangle(self.x, self.y, self.width, self.height, color=aj.c_blue)

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

levels: list[aj.GameLevel] = aj.load_ldtk_levels(Path(__file__).parent / 'room_data' / 'test' / 'simplified')
aj.set_rooms(levels)
aj.register_objects(Floor, Player, Camera)

aj.room_set_caption("Platformer")
aspect_ratio: float = levels[0].level_size[0] / levels[0].level_size[1]
aj.window_set_size(960, int(960 / aspect_ratio))
aj.game_start()