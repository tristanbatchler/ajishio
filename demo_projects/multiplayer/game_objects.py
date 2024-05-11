import ajishio as aj
from uuid import UUID

class Player(aj.GameObject):
    def __init__(self, player_id: UUID, x: float, y: float, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player_id = player_id
        self.x = x
        self.y = y
        self.speed = 4

    def move(self, input_x: float, input_y: float) -> None:
        self.x += input_x * self.speed
        self.y += input_y * self.speed

    def draw(self) -> None:
        aj.draw_circle(self.x, self.y, 8, aj.Color(255, 255, 255))