import math
from random import uniform, choice
from typing import Literal
import ajishio as aj

class Wall(aj.GameObject):
    def __init__(self, width: float, height: float, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.collision_mask = aj.CollisionMask(
            bbtop=0,
            bbleft=0,
            bbright=width,
            bbbottom=height
        )
        self.width: float = width
        self.height: float = height

    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, self.width, self.height, False)

class Boundary(Wall):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def draw(self) -> None:
        super().draw()

class Paddle(Wall):
    def __init__(self, player: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.speed: float = 5
        self.y_vel: float = 0
        
        self.up_key: int = ord('w') if player == 1 else aj.vk_up
        self.down_key: int = ord('s') if player == 1 else aj.vk_down

    def step(self) -> None:
        self.y_vel = (aj.keyboard_check(self.down_key) - aj.keyboard_check(self.up_key)) * self.speed
        self.target_y = self.y + self.y_vel
        if self.place_meeting(self.x, self.target_y, Boundary):
            while not self.place_meeting(self.x, self.y + aj.sign(self.y_vel), Boundary):
                self.y += aj.sign(self.y_vel)
            self.y_vel = 0
        else:
            self.y = self.target_y


class Ball(aj.GameObject):
    def __init__(self, radius: float, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.radius: float = radius

        self.collision_mask = aj.CollisionMask(
            bbleft=-self.radius,
            bbtop=-self.radius,
            bbright=self.radius,
            bbbottom=self.radius,
        )

        self.speed: float = 3
        self.speed_increase_percent: float = 1.05
        self.max_speed: float = 8

        self.score: dict[int, int] = {1: 0, 2: 0}

        self.max_y_dir: float = 0.5

        self.color_hue_angle: float = 0

        # Direction will be set by the reset method
        self.x_dir: float
        self.y_dir: float
        self.reset()

    def step(self) -> None:
        x_vel: float = self.x_dir * self.speed
        y_vel: float = self.y_dir * self.speed

        hit_x: aj.GameObject | None = self.place_meeting(self.x + x_vel, self.y, Wall)
        if hit_x:
            while not self.place_meeting(self.x + aj.sign(x_vel), self.y, Wall):
                self.x += aj.sign(x_vel)
            x_vel = 0
            self.x_dir *= -1

            if isinstance(hit_x, Paddle):
                added_y_vel: float = hit_x.y_vel / (4 * hit_x.speed)
                self.y_dir = aj.clamp(self.y_dir + added_y_vel, -self.max_y_dir, self.max_y_dir)
                self.set_x_dir(aj.sign(self.x_dir))
                self.speed = aj.clamp(self.speed * self.speed_increase_percent, self.speed, self.max_speed)
                self.color_hue_angle += 0.1

        if self.place_meeting(self.x, self.y + y_vel, Wall):
            while not self.place_meeting(self.x, self.y + aj.sign(y_vel), Wall):
                self.y += aj.sign(y_vel)
            y_vel = 0
            self.y_dir *= -1
        
        self.x += x_vel
        self.y += y_vel

        winner: int = self.out_of_bounds()
        if winner != 0:
            self.update_score(winner)
            self.reset()
        
        if self.score[1] >= 10 or self.score[2] >= 10:
            self.speed = 0
            self.color_hue_angle += 0.01

    def out_of_bounds(self) -> Literal[0, 1, 2]:
        buffer: float = 100
        return 2 if self.x < -self.radius - buffer else 1 if self.x > aj.room_width + self.radius + buffer else 0

    def update_score(self, winner: int) -> None:
        self.score[winner] += 1

    def reset(self) -> None:
        self.x = aj.room_width / 2
        self.y = aj.room_height / 2
        self.y_dir = uniform(-self.max_y_dir, self.max_y_dir)
        self.set_x_dir(choice([-1, 1]))
        
    def set_x_dir(self, sign: int) -> None:
        if sign not in (-1, 1):
            raise ValueError("sign must be -1 or 1")
        self.x_dir = sign * math.sqrt(1 - self.y_dir ** 2)

    def draw(self) -> None:
        aj.draw_circle(self.x, self.y, self.radius, aj.make_color_hsv(self.color_hue_angle, 1, 1))
        aj.draw_text(20, 20, str(self.score[1]))
        aj.draw_text(aj.room_width - 50, 20, str(self.score[2]))

        speed_text: str = f"SPEED: {self.speed:.2f}"
        aj.draw_text((aj.room_width - aj.text_width(speed_text)) / 2, 20, speed_text, color=aj.make_color_hsv(self.color_hue_angle, 1, 1))

def main() -> None:
    aj.room_set_caption("Pong")
    wall_width: float = 5
    paddle_height: float = 100
    paddle_buffer: float = 100
    Boundary(x=0, y=0, width=aj.room_width, height=wall_width)
    Boundary(x=0, y=aj.room_height-wall_width, width=aj.room_width, height=wall_width)
    Paddle(x=paddle_buffer, y=(aj.room_height-paddle_height)/2, width=wall_width, height=paddle_height, player=1)
    Paddle(x=aj.room_width-paddle_buffer-wall_width, y=(aj.room_height-paddle_height)/2, width=wall_width, height=paddle_height, player=2)
    Ball(radius=7.5)
    aj.game_start()


if __name__ == '__main__':
    main()
