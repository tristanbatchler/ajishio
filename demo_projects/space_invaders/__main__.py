import ajishio as aj
import random

PADDING: int = 64
level: int = 1


class Player(aj.GameObject):
    width = 32
    height = 32

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.speed = 5.0
        self.x = aj.room_width / 2.0
        self.y = aj.room_height - PADDING
        self.collision_mask = aj.CollisionMask(0, 0, Player.width, Player.height)
        self.bullet_speed = 10.0
        self.lives: int = 3

    def step(self) -> None:
        x_input = aj.keyboard_check(aj.vk_right) - aj.keyboard_check(aj.vk_left)

        self.x += x_input * self.speed

        if aj.keyboard_check_released(aj.vk_space):
            Bullet(self.x + Player.width / 2, self.y, -self.bullet_speed, hurts_player=False)

        if self.lives <= 0:
            aj.instance_destroy(self)
            aj.game_set_speed(0)

    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, Player.width, Player.height, color=aj.c_lime)

        fps_caption = f"FPS: {aj.fps_real:.2f}"
        aj.draw_rectangle(
            10,
            10,
            aj.text_width(fps_caption) + 10,
            aj.text_height(fps_caption) + 10,
            color=aj.c_black,
            alpha=0.5,
        )
        aj.draw_text(10, 10, fps_caption, color=aj.c_white)

        lives_caption = f"Lives: {self.lives}"
        aj.draw_rectangle(
            aj.room_width - aj.text_width(lives_caption) - 10,
            10,
            aj.text_width(lives_caption) + 10,
            aj.text_height(lives_caption) + 10,
            color=aj.c_black,
            alpha=0.5,
        )
        aj.draw_text(
            aj.room_width - aj.text_width(lives_caption) - 10, 10, lives_caption, aj.c_white
        )


class Enemy(aj.GameObject):
    width = 32.0
    height = 32.0

    def __init__(self, x: float, y: float, x_velocity: float, *args, **kwargs) -> None:
        super().__init__(x, y, *args, **kwargs)
        self.x_velocity = x_velocity
        self.bullet_speed = 8.0
        self.collision_mask = aj.CollisionMask(0, 0, Enemy.width, Enemy.height)

    def step(self) -> None:
        if not (0 <= self.x <= aj.room_width - Enemy.width):
            self.x_velocity *= -1
            self.y += Enemy.height
        self.x = aj.clamp(self.x, 0, aj.room_width - Enemy.width)
        self.x += self.x_velocity

        if random.random() < 0.0005:
            Bullet(
                self.x, self.y + Enemy.width / 2.0, y_velocity=self.bullet_speed, hurts_player=True
            )

        if player := self.place_meeting(self.x, self.y, Player):
            aj.instance_destroy(player)
            aj.game_set_speed(0)

    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, Enemy.width, Enemy.height, color=aj.c_purple)


class Bullet(aj.GameObject):
    width = 4
    height = 8

    def __init__(
        self, x: float, y: float, y_velocity: float, hurts_player: bool, *args, **kwargs
    ) -> None:
        super().__init__(x, y, *args, *kwargs)
        self.y_velocity = y_velocity
        self.hurts_player = hurts_player
        self.collision_mask = aj.CollisionMask(0, 0, Bullet.width, Bullet.height)

    def step(self) -> None:
        self.y += self.y_velocity
        if not (0 <= self.y <= aj.room_height - Bullet.height):
            aj.instance_destroy(self)

        if self.hurts_player and (player := self.place_meeting(self.x, self.y, Player)):
            aj.instance_destroy(self)
            assert isinstance(player, Player)
            player.lives -= 1

        elif not self.hurts_player and (enemy := self.place_meeting(self.x, self.y, Enemy)):
            aj.instance_destroy(self)
            aj.instance_destroy(enemy)
            if not aj.instance_exists(Enemy):
                global level
                level += 1
                spawn_wave(level)

    def draw(self) -> None:
        aj.draw_rectangle(self.x, self.y, Bullet.width, Bullet.height, color=aj.c_black)


def spawn_wave(difficulty: int) -> None:
    speed = 2 ** (difficulty / 5.0)  # Gets exponentially harder each wave
    for row in range(3):
        for enemy_x in range(PADDING, aj.room_width - PADDING, round(1.5 * Enemy.width)):
            Enemy(enemy_x, PADDING + Enemy.height * row * 1.5, x_velocity=speed)


def main() -> None:

    Player()

    aj.register_objects(Player, Enemy, Bullet)
    spawn_wave(level)

    aj.room_set_caption("Space Invaders")
    aj.room_set_background(aj.c_teal)
    aj.game_start()


if __name__ == "__main__":
    main()
