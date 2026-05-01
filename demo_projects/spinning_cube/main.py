import ajishio as aj
from dataclasses import dataclass, astuple
from typing import override, Unpack
from math import sin, cos, sqrt
from collections.abc import Iterator


@dataclass
class Point:
    x: float
    y: float
    z: float

    @override
    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"

    def __iter__(self) -> Iterator[float]:
        return iter(astuple(self))


CUBE_SIDE: float = 1.0
HALF_CUBE_SIDE: float = CUBE_SIDE / 2
CUBE_ORIGIN: Point = Point(0, 0, 0)

X_MIN = CUBE_ORIGIN.x - HALF_CUBE_SIDE
X_MAX = CUBE_ORIGIN.x + HALF_CUBE_SIDE
Y_MIN = CUBE_ORIGIN.y - HALF_CUBE_SIDE
Y_MAX = CUBE_ORIGIN.y + HALF_CUBE_SIDE
Z_MIN = CUBE_ORIGIN.z - HALF_CUBE_SIDE
Z_MAX = CUBE_ORIGIN.z + HALF_CUBE_SIDE


def get_points(resolution: int) -> list[Point]:
    points: list[Point] = []
    step = CUBE_SIDE / resolution

    for xi in range(resolution + 1):
        x = X_MAX if xi == resolution else X_MIN + xi * step
        on_x_bounds = xi == 0 or xi == resolution

        for yi in range(resolution + 1):
            y = Y_MAX if yi == resolution else Y_MIN + yi * step
            on_y_bounds = yi == 0 or yi == resolution

            for zi in range(resolution + 1):
                z = Z_MAX if zi == resolution else Z_MIN + zi * step
                on_z_bounds = zi == 0 or zi == resolution

                # Only interested in outer shell
                if any((on_x_bounds, on_y_bounds, on_z_bounds)):
                    points.append(Point(x, y, z))

    return points


def matrix_rot_x(a: float) -> list[list[float]]:
    return [[1, 0, 0], [0, cos(a), -sin(a)], [0, sin(a), cos(a)]]


def matrix_rot_y(a: float) -> list[list[float]]:
    return [[cos(a), 0, sin(a)], [0, 1, 0], [-sin(a), 0, cos(a)]]


def matrix_rot_z(a: float) -> list[list[float]]:
    return [[cos(a), -sin(a), 0], [sin(a), cos(a), 0], [0, 0, 1]]


def dot(row: list[float], point: Point) -> float:
    assert len(row) == 3, "Dot product with row, but row isn't 3 elements??"
    return row[0] * point.x + row[1] * point.y + row[2] * point.z


def multiply(matrix: list[list[float]], point: Point) -> Point:
    assert len(matrix) == 3, "Multiply with matrix, but matrix isn't 3 rows??"
    new_x = dot(matrix[0], point)
    new_y = dot(matrix[1], point)
    new_z = dot(matrix[2], point)

    return Point(new_x, new_y, new_z)


def remap_range(n: float, old_min: float, old_max: float, new_min: float, new_max: float) -> float:
    return (n - old_min) / (old_max - old_min) * (new_max - new_min) + new_min


def rotate_x(points: list[Point], radians: float) -> None:
    for i in range(len(points)):
        points[i] = multiply(matrix_rot_x(radians), points[i])


def rotate_y(points: list[Point], radians: float) -> None:
    for i in range(len(points)):
        points[i] = multiply(matrix_rot_y(radians), points[i])


def rotate_z(points: list[Point], radians: float) -> None:
    for i in range(len(points)):
        points[i] = multiply(matrix_rot_z(radians), points[i])


class SpinningCube(aj.GameObject):
    def __init__(
        self, points: list[Point], x: float = 0, y: float = 0, **kwargs: Unpack[aj.GameObjectKwargs]
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.points: list[Point] = points
        self.scale: float = self.get_scale()
        self.circle_radius: float = self.get_circle_radius()
        self.mouse_start_drag_x: float = aj.mouse_x
        self.mouse_start_drag_y: float = aj.mouse_y
        self.viewer_distance: float = 3.0
        self.spin_pitch_velocity: float = 0.0
        self.spin_roll_velocity: float = 0.0
        self.friction: float = 0.98
        self.friction_enabled: bool = True

    def get_scale(self) -> float:
        padding = 20
        return 0.5 * (min(aj.room_width, aj.room_height) / CUBE_SIDE) - padding

    def get_circle_radius(self) -> float:
        n_points = len(self.points)
        if n_points <= 8:
            return 2.0

        return self.scale * 0.45 * sqrt(6.0 / max(1, n_points - 2))

    @override
    def step(self) -> None:
        super().step()

        pitch_amount = self.spin_pitch_velocity * aj.delta_time
        roll_amount = self.spin_roll_velocity * aj.delta_time

        if aj.mouse_check_button(aj.mb_left):
            dx = aj.mouse_x - self.mouse_start_drag_x
            dy = aj.mouse_y - self.mouse_start_drag_y

            sensitivity = 0.8

            self.spin_pitch_velocity = -dx * sensitivity
            self.spin_roll_velocity = dy * sensitivity

            pitch_amount = self.spin_pitch_velocity * aj.delta_time
            roll_amount = self.spin_roll_velocity * aj.delta_time
        elif self.friction_enabled:
            self.spin_pitch_velocity *= self.friction
            self.spin_roll_velocity *= self.friction

        if aj.mouse_wheel_up():
            self.viewer_distance -= 5 * aj.delta_time
        if aj.mouse_wheel_down():
            self.viewer_distance += 5 * aj.delta_time

        if aj.keyboard_check_pressed(aj.vk_space):
            self.friction_enabled = not self.friction_enabled

        rotate_y(self.points, pitch_amount)
        rotate_x(self.points, roll_amount)

        self.mouse_start_drag_x = aj.mouse_x
        self.mouse_start_drag_y = aj.mouse_y

    def draw_point(self, x: float, y: float, z: float):
        fov = 600
        projected_z = z + self.viewer_distance

        if projected_z <= 0.1:  # Prevent division by zero or clipping behind camera
            return

        f = fov / projected_z

        z_near = Z_MIN + self.viewer_distance
        z_far = Z_MAX + self.viewer_distance

        lightness = remap_range(projected_z, z_near, z_far, 1.0, 0.2)
        lightness = aj.clamp(lightness, 0, 1)

        hue = remap_range(projected_z, z_near, z_far, 0.45, 0.7)
        hue = aj.clamp(hue, 0, 1)

        color = aj.make_color_hsv(hue, 1, lightness)

        aj.draw_circle(
            aj.room_width / 2 + (x * f),
            aj.room_height / 2 + (y * f),
            radius=self.circle_radius * (f / 300),
            color=color,
        )

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_text(10, 10, "LMB: rotate cube")
        aj.draw_text(10, 30, "Mouse wheel: zoom")
        aj.draw_text(10, 50, "Space: friction " + ("off" if self.friction_enabled else "on"))
        for point in sorted(self.points, key=lambda p: p.z, reverse=True):
            self.draw_point(*point)


def main():
    points = get_points(15)
    _ = SpinningCube(points)
    aj.room_set_size(1280, 720)
    aj.window_set_size(1280, 720)
    aj.room_set_caption("Spinning Cube")
    aj.game_start()


if __name__ == "__main__":
    main()
