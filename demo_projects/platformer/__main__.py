import ajishio as aj
from pathlib import Path
import csv
import json
from typing import Any

aj.room_set_caption("Platformer")

# Define a class for the floor
class Floor(aj.GameObject):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=tile_width,
            bbbottom=tile_height
        )

# Load the level
cwd: Path = Path(__file__).parent
level_dir: Path = cwd / 'room_data' / 'test' / 'simplified' / 'Level_0'

ground_data: list[list[bool]] = []
with open(level_dir / 'GroundIntLayer.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        ground_data.append([bool(int(cell)) for cell in row if cell != ''])

level_info: dict[str, Any] = json.loads((level_dir / 'data.json').read_text())
level_width: int = level_info['width']
level_height: int = level_info['height']

tile_width: int = level_width // len(ground_data[0])
tile_height: int = level_height // len(ground_data)

for y, row in enumerate(ground_data):
    for x, cell in enumerate(row):
        if cell:
            Floor(x * tile_width, y * tile_height)

# Draw the level
with open(level_dir / '_composite.png', 'rb') as f:
    aj.room_set_background_image(f)

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
        self.jump_height: float = -10

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

        if self.place_meeting(self.x, self.y + 1, Floor):
            if aj.keyboard_check(aj.vk_space):
                self.y_velocity = self.jump_height

    def draw(self):
        aj.draw_rectangle(self.x, self.y, self.width, self.height, color=aj.c_blue)

# Load the entities (in this case, just the player)
player_data: dict[str, Any] = level_info['entities']['Player'][0]

# Create the player
Player(player_data['x'], player_data['y'], width=player_data['width'], height=player_data['height'], speed=3)

aj.game_start()