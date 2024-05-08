import ajishio as aj
from random import choice, randrange

class GridAlignedObject(aj.GameObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.collision_mask: aj.CollisionMask = aj.CollisionMask(
            bbtop=0, bbleft=0, bbright=GRID_SIZE, bbbottom=GRID_SIZE
        )

        self.grid_x: int = -1
        self.grid_y: int = -1

        self.previous_grid_x: int
        self.previous_grid_y: int

    def step(self) -> None:
        self.previous_grid_x = self.grid_x
        self.previous_grid_y = self.grid_y

    def update_position(self) -> None:
        self.previous_x = self.x
        self.previous_y = self.y

        if self.grid_x < 0:
            self.grid_x = NUM_COLS - 1
        elif self.grid_x >= NUM_COLS:
            self.grid_x = 0
        if self.grid_y < 0:
            self.grid_y = NUM_ROWS - 1
        elif self.grid_y >= NUM_ROWS:
            self.grid_y = 0
        self.x = self.grid_x * GRID_SIZE
        self.y = self.grid_y * GRID_SIZE

    def draw_self(self, color: aj.Color=aj.c_white):
        aj.draw_rectangle(self.x, self.y, GRID_SIZE, GRID_SIZE, color=color)

class Apple(GridAlignedObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.grid_x = randrange(0, NUM_COLS)
        self.grid_y = randrange(0, NUM_ROWS)
        self.update_position()

    def draw(self) -> None:
        self.draw_self(color=aj.c_red)

class SnakeHead(GridAlignedObject):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.grid_x: int = NUM_COLS // 2
        self.grid_y: int = NUM_ROWS // 2

        self.update_position()

        self.x_velocity: int = choice((-1, 0, 1))
        self.y_velocity: int = choice((-1, 1)) * (1 - abs(self.x_velocity))
        
        self.tail_segments: list[SnakeTailSegment] = [SnakeTailSegment(self, i) for i in range(3)]

    def step(self) -> None:
        super().step()

        if self.y_velocity == 0:
            if aj.keyboard_check_pressed(aj.vk_up):
                    self.x_velocity = 0
                    self.y_velocity = -1
            elif aj.keyboard_check_pressed(aj.vk_down):
                self.x_velocity = 0
                self.y_velocity = 1
        
        elif self.x_velocity == 0:
            if aj.keyboard_check_pressed(aj.vk_left):
                self.x_velocity = -1
                self.y_velocity = 0
            elif aj.keyboard_check_pressed(aj.vk_right):
                self.x_velocity = 1
                self.y_velocity = 0

        self.grid_x += self.x_velocity
        self.grid_y += self.y_velocity
        self.update_position()

        hit_apple: aj.GameObject | None = self.place_meeting(self.x, self.y, Apple)
        if hit_apple:
            aj.game_set_speed(aj.room_speed * 1.05)
            self.tail_segments.append(SnakeTailSegment(self, len(self.tail_segments)))
            aj.instance_destroy(hit_apple)
            Apple()

        if aj.GameObject.place_meeting(self, self.x, self.y, SnakeTailSegment):
            global game_over
            game_over = True

    def draw(self) -> None:
        self.draw_self()
        if game_over:
            text: str = "Game Over"
            aj.draw_text((aj.room_width - aj.text_width(text)) / 2, (aj.room_height - aj.text_height(text)) / 2, text, color=aj.c_white)
            aj.game_set_speed(0)



class SnakeTailSegment(GridAlignedObject):
    def __init__(self, head: SnakeHead, index: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.head: SnakeHead = head
        self.index: int = index

    def step(self) -> None:
        super().step()
        in_front: SnakeHead | SnakeTailSegment = self.head if self.index == 0 else self.head.tail_segments[self.index - 1]
        self.grid_x = in_front.previous_grid_x
        self.grid_y = in_front.previous_grid_y
        self.update_position()
        
    def draw(self) -> None:
        self.draw_self(color=aj.c_ltgray)


GRID_SIZE: int = 16
NUM_COLS: int = aj.room_width // GRID_SIZE
NUM_ROWS: int = aj.room_height // GRID_SIZE
game_over: bool = False

aj.room_set_caption("Snake")
aj.room_set_background(aj.c_purple)
SnakeHead()
Apple()

# Note: setting the game speed like this is not recommended, as it can lead to inconsistent input handling
aj.game_set_speed(5)
aj.game_start()