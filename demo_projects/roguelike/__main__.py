import ajishio as aj
from pathlib import Path
from typing import Any
import pygame as pg

GRID_SIZE = 32

class Wall(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.collision_mask = aj.CollisionMask(bbleft=0, bbtop=0, bbright=self.width, bbbottom=self.height)

class Doorway(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        if GRID_SIZE not in (self.width, self.height):
            raise ValueError("Doorway must be a single tile in width or height")
            
        self.collision_mask = aj.CollisionMask(bbleft=0, bbtop=0, bbright=self.width, bbbottom=self.height)

        self.to_room: int = self.custom_fields.get("to_room", 0)
        self.to_doorway_iid: str | None = self.custom_fields.get("to_doorway", {}).get("entityIid", None)

class Player(aj.GameObject):
    persistent: bool = True

    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.sprite_index = sprites['player']
        self.grid_x: int = int(x / GRID_SIZE)
        self.grid_y: int = int(y / GRID_SIZE)
        self.target_grid_x: int = self.grid_x
        self.target_grid_y: int = self.grid_y
        self.collision_mask = aj.CollisionMask(bbleft=0, bbtop=0, bbright=self.sprite_width, bbbottom=self.sprite_height)
        self.last_x_direction: int = 0
        self.last_y_direction: int = 0

    def step(self) -> None:
        super().step()
        self.x = self.grid_x * GRID_SIZE
        self.y = self.grid_y * GRID_SIZE

        if aj.keyboard_check_pressed(aj.vk_up):
            self.target_grid_y -= 1
            self.last_x_direction = 0
            self.last_y_direction = -1
        elif aj.keyboard_check_pressed(aj.vk_down):
            self.target_grid_y += 1
            self.last_x_direction = 0
            self.last_y_direction = 1
        elif aj.keyboard_check_pressed(aj.vk_left):
            self.target_grid_x -= 1
            self.last_x_direction = -1
            self.last_y_direction = 0
        if aj.keyboard_check_pressed(aj.vk_right):
            self.target_grid_x += 1
            self.last_x_direction = 1
            self.last_y_direction = 0

        if not self.place_meeting(self.target_grid_x * GRID_SIZE, self.target_grid_y * GRID_SIZE, Wall):
            self.grid_x = self.target_grid_x
            self.grid_y = self.target_grid_y
        else:
            self.target_grid_x = self.grid_x
            self.target_grid_y = self.grid_y

        doorway_hit: aj.GameObject | None = self.place_meeting(self.x, self.y, Doorway)
        if doorway_hit and isinstance(doorway_hit, Doorway):
            aj.room_goto(doorway_hit.to_room)
            if doorway_hit.to_doorway_iid:
                to_doorway: aj.GameObject | None = aj.instance_find(doorway_hit.to_doorway_iid)
                if to_doorway and isinstance(to_doorway, Doorway):
                    self.grid_x = int(to_doorway.x / GRID_SIZE) + self.last_x_direction
                    self.grid_y = int(to_doorway.y / GRID_SIZE) + self.last_y_direction



project_dir = Path(__file__).parent


rooms: list[aj.GameLevel] = aj.load_ldtk_levels(project_dir / "rooms" / "rooms" / "simplified")

aj.set_rooms(rooms)
aj.register_objects(Wall, Doorway, Player)

sprites: dict[str, aj.GameSprite] = aj.load_aseprite_sprites(project_dir / "sprites")

aj.room_set_caption("Roguelike")
aspect_ratio: float = rooms[0].level_size[0] / rooms[0].level_size[1]
aj.window_set_size(960, int(960 / aspect_ratio))

aj.room_set_background(aj.Color(20, 20, 20))

aj.game_start()