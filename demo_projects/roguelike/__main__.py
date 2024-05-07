import ajishio as aj
from pathlib import Path

GRID_SIZE = 32

class Wall(aj.GameObject):
    def __init__(self, x: float, y: float, width: float, height: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.collision_mask = aj.CollisionMask(bbleft=0, bbtop=0, bbright=width, bbbottom=height)

class Doorway(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.width = kwargs.get("width", 32)
        self.height = kwargs.get("height", 32)
        self.to_room: int = kwargs.get("customFields", {}).get("to_room", 0)
        self.collision_mask = aj.CollisionMask(bbleft=0, bbtop=0, bbright=self.width, bbbottom=self.height)

class Player(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.sprite_index = sprites['player']
        self.grid_x = x // GRID_SIZE
        self.grid_y = y // GRID_SIZE
        self.collision_mask = aj.CollisionMask(bbleft=0, bbtop=0, bbright=self.sprite_width, bbbottom=self.sprite_height)

    def step(self) -> None:
        super().step()
        self.x = self.grid_x * GRID_SIZE
        self.y = self.grid_y * GRID_SIZE


        target_grid_x = self.grid_x
        target_grid_y = self.grid_y
        if aj.keyboard_check(aj.vk_up):
            target_grid_y -= 1
        elif aj.keyboard_check(aj.vk_down):
            target_grid_y += 1
        elif aj.keyboard_check(aj.vk_left):
            target_grid_x -= 1
        elif aj.keyboard_check(aj.vk_right):
            target_grid_x += 1

        if not self.place_meeting(target_grid_x * GRID_SIZE, target_grid_y * GRID_SIZE, Wall):
            self.grid_x = target_grid_x
            self.grid_y = target_grid_y

        doorway_hit: aj.GameObject | None = self.place_meeting(self.x, self.y, Doorway)
        if doorway_hit:
            assert isinstance(doorway_hit, Doorway)
            aj.room_goto(doorway_hit.to_room)



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