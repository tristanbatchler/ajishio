import ajishio as aj
from demo_projects.multiplayer.shared import sprites

class PlayerSpawner(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)

    def draw(self) -> None:
        super().draw()
        # Debug
        aj.draw_rectangle(self.x, self.y, self.width, self.height, outline=True, color=aj.Color(0, 255, 0))

class Floor(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs):
        super().__init__(x, y, *args, **kwargs)
        self.collision_mask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=self.width,
            bbbottom=self.height
        )

    def draw(self) -> None:
        super().draw()
        # Debug
        aj.draw_rectangle(self.x, self.y, self.width, self.height, outline=True, color=aj.Color(255, 0, 0))

class Player(aj.GameObject):
    def __init__(self, x: float, y: float, *args, **kwargs) -> None:
        super().__init__(x, y, *args, **kwargs)
        self.sprite_index = sprites["player"]
        self.image_speed = 10
        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=2,
            bbleft=5,
            bbright=self.sprite_width - 5,
            bbbottom=self.sprite_height
        )

        self.input_x: int = 0

        self.x_velocity: float = 0.0
        self.y_velocity: float = 0.0

        self.speed = 3.0 * aj.room_speed
        self.jump_height: float = -10 * aj.room_speed
        self.max_fall_speed: float = 12 * aj.room_speed

        self.gravity: float = 1.0 * aj.room_speed**2
        self.acceleration: float = 1.0 * aj.room_speed**2

    def jump(self) -> None:
        if self.place_meeting(self.x, self.y + 1, Floor):
            self.y_velocity = self.jump_height

    def step(self) -> None:
        super().step()

        # Apply gravity
        self.y_velocity += self.gravity * aj.delta_time
        if self.y_velocity > self.max_fall_speed:
            self.y_velocity = self.max_fall_speed

        # Calculate x velocity
        a_dt = self.acceleration * aj.delta_time

        if self.input_x != 0:
            self.x_velocity += self.input_x * a_dt
        else:
            self.x_velocity -= aj.sign(self.x_velocity) * a_dt
        
        if abs(self.x_velocity) < a_dt:
            self.x_velocity = 0

        self.x_velocity = aj.clamp(self.x_velocity, -self.speed, self.speed)

        # Move x
        target_x = self.x + self.x_velocity * aj.delta_time
        if self.place_meeting(target_x, self.y, Floor):
            while not self.place_meeting(self.x + aj.sign(self.x_velocity), self.y, Floor):
                self.x += aj.sign(self.x_velocity)
            self.x_velocity = 0
        else:
            self.x = target_x

        # Move y
        target_y = self.y + self.y_velocity * aj.delta_time
        if self.place_meeting(self.x, target_y, Floor):
            while not self.place_meeting(self.x, self.y + aj.sign(self.y_velocity), Floor):
                self.y += aj.sign(self.y_velocity)
            self.y_velocity = 0
        else:
            self.y = target_y
