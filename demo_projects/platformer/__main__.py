import ajishio as aj
from pathlib import Path
from typing import Any

aj.room_set_caption("Platformer")

# Define a class for the floor
class Floor(aj.GameObject):
    def __init__(self, x: float, y: float, tile_width: int, tile_height: int):
        super().__init__(x, y)
        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=tile_width,
            bbbottom=tile_height
        )

level: aj.GameLevel = aj.load_ldtk(Path(__file__).parent / 'room_data' / 'test' / 'simplified' / 'Level_0')

for y, row in enumerate(level.tilemap):
    for x, cell in enumerate(row):
        if cell:
            Floor(x * level.tile_size[0], y * level.tile_size[1], *level.tile_size)

# Draw the level
aj.room_set_background_image(level.background_surface)

# Define the player
class Player(aj.GameObject):
    def __init__(self, x: float, y: float, width: float = 16, height: float = 32, speed: float = 5):
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

    def step(self):
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

    def draw(self):
        aj.draw_rectangle(self.x, self.y, self.width, self.height, color=aj.c_blue)

# Load the entities (in this case, just the player)
player_data: dict[str, Any] = level.entities['Player'][0]

# Create the player
player_x: float = player_data['x']
player_y: float = player_data['y']
player = Player(player_x, player_y, width=player_data['width'], height=player_data['height'], speed=3)


# Define the camera
class Camera(aj.GameObject):
    def __init__(self, following: aj.GameObject):
        super().__init__(following.x, following.y)
        self.following: aj.GameObject = following

    def step(self):
        self.x = self.following.x
        self.y = self.following.y

        aj.view_xport[aj.view_current] = self.x - aj.view_wport[aj.view_current] // 2
        aj.view_yport[aj.view_current] = self.y - aj.view_hport[aj.view_current] // 2

# Create the camera
Camera(player)

# Set the display size
aj.view_set_wport(aj.view_current, 400)
aj.view_set_hport(aj.view_current, 300)

print(aj.view_wport[aj.view_current], aj.view_hport[aj.view_current])

aj.game_start()