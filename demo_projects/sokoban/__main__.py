import ajishio as aj
from pathlib import Path


class Player(aj.GameObject):
    def __init__(self, radius: float, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.radius = radius

    def step(self) -> None:
        dx, dy = 0, 0
        if aj.keyboard_check_pressed(aj.vk_right):
            dx = 1
        elif aj.keyboard_check_pressed(aj.vk_left):
            dx = -1
        if aj.keyboard_check_pressed(aj.vk_down):
            dy = 1
        elif aj.keyboard_check_pressed(aj.vk_up):
            dy = -1

        # Level controls
        if aj.keyboard_check_pressed(aj.ord("R")):
            level.restart()
            return
        if aj.keyboard_check_pressed(aj.ord("N")):
            if level.next_level():
                print(f"Skipped to {level.get_level_info()}")
            return
        if aj.keyboard_check_pressed(aj.ord("P")):
            if level.previous_level():
                print(f"Back to {level.get_level_info()}")
            return
        if dx == 0 and dy == 0:
            return
        if abs(dx) + abs(dy) > 1:
            return

        target_pos = (int(self.x) + dx, int(self.y) + dy)

        if target_pos in level.walls:
            return

        if crate := level.crates.get(target_pos):
            if not crate.move(dx, dy):
                return

        self.x, self.y = target_pos

    def draw(self) -> None:
        x = level.offset_x + self.x * level.grid_size + level.half_grid_size
        y = level.offset_y + self.y * level.grid_size + level.half_grid_size
        aj.draw_circle(x, y, self.radius, aj.c_lime)


class Wall(aj.GameObject):
    def draw(self) -> None:
        aj.draw_rectangle(
            level.offset_x + self.x * level.grid_size,
            level.offset_y + self.y * level.grid_size,
            level.grid_size,
            level.grid_size,
            color=aj.c_black,
        )


class Crate(Wall):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.depth = -1  # Ensure crates are drawn on top of everything else

    def draw(self) -> None:
        x = level.offset_x + self.x * level.grid_size + level.half_grid_size
        y = level.offset_y + self.y * level.grid_size + level.half_grid_size
        aj.draw_rectangle(
            x - level.half_grid_size * 0.8,
            y - level.half_grid_size * 0.8,
            level.grid_size * 0.8,
            level.grid_size * 0.8,
            color=aj.c_aqua,
        )

    def move(self, dx: int, dy: int) -> bool:
        target_pos = (int(self.x) + dx, int(self.y) + dy)
        if target_pos in level.walls or target_pos in level.crates:
            return False

        level.crates.pop((int(self.x), int(self.y)), None)
        level.crates[target_pos] = self
        self.x, self.y = target_pos
        level.check_completion()
        return True


class Goal(aj.GameObject):
    def draw(self) -> None:
        aj.draw_rectangle(
            level.offset_x + self.x * level.grid_size,
            level.offset_y + self.y * level.grid_size,
            level.grid_size,
            level.grid_size,
            color=aj.c_red,
        )


class Level:
    def __init__(self, levels_file: Path) -> None:
        self.walls: dict[tuple[int, int], Wall] = {}
        self.player: Player | None = None
        self.goals: dict[tuple[int, int], Goal] = {}
        self.crates: dict[tuple[int, int], Crate] = {}

        self._levels_file = levels_file
        self._index = 1
        self.width: int = 0
        self.height: int = 0
        self.grid_size: int = 0
        self.half_grid_size: int = 0
        self._levels_data = self._parse_levels_file()
        self._max_level = len(self._levels_data)
        self._load_level()

    def _parse_levels_file(self) -> dict[int, list[str]]:
        """Parse the levels.txt file and return a dictionary of level data."""
        levels = {}
        current_level = 0
        current_lines: list[str] = []

        with open(self._levels_file, "r") as f:
            for line in f:
                line = line.rstrip()

                # Check if this is a level header
                if line.startswith("Level:"):
                    # Save previous level if exists
                    if current_level > 0 and current_lines:
                        # Remove empty lines from end
                        while current_lines and not current_lines[-1].strip():
                            current_lines.pop()
                        levels[current_level] = current_lines

                    # Start new level (increment counter since levels don't have explicit numbers)
                    current_level += 1
                    current_lines = []

                # Skip empty lines at start of level
                elif not line.strip() and not current_lines:
                    continue

                # Add level data line (skip the header line itself)
                elif current_level > 0 and not line.startswith("Level:"):
                    current_lines.append(line)

        # Don't forget the last level
        if current_level > 0 and current_lines:
            while current_lines and not current_lines[-1].strip():
                current_lines.pop()
            levels[current_level] = current_lines

        return levels

    def _get_current_level_data(self) -> list[str]:
        """Get the current level's data lines."""
        return self._levels_data.get(self._index, [])

    def _load_level(self) -> None:
        # Clear any existing objects first
        self._clear_level()

        # Reset the level state
        self.walls.clear()
        self.goals.clear()
        self.crates.clear()
        self.player = None
        self.width = 0
        self.height = 0

        # Update window title with current level
        aj.room_set_caption(f"Sokoban - {self.get_level_info()}")

        level_lines = self._get_current_level_data()

        player_pos: tuple[int, int] | None = None
        for y, line in enumerate(level_lines):
            for x, c in enumerate(line):
                coord = (x, y)
                match c:
                    case "#":
                        self.walls[coord] = Wall(x=x, y=y)
                    case ".":
                        self.goals[coord] = Goal(x=x, y=y)
                    case "X":
                        self.goals[coord] = Goal(x=x, y=y)
                        self.crates[coord] = Crate(x=x, y=y)
                    case "*":
                        self.goals[coord] = Goal(x=x, y=y)
                        self.crates[coord] = Crate(x=x, y=y)
                    case "B":
                        self.crates[coord] = Crate(x=x, y=y)
                    case "$":
                        self.crates[coord] = Crate(x=x, y=y)
                    case "&":
                        player_pos = (x, y)
                    case "@":
                        player_pos = (x, y)
                    case "+":
                        self.goals[coord] = Goal(x=x, y=y)
                        player_pos = (x, y)

                if x + 1 > self.width:
                    self.width = x + 1
            if y + 1 > self.height:
                self.height = y + 1

        self.grid_size = min(
            aj.window_width // self.width,
            aj.window_height // self.height,
        )
        self.half_grid_size = self.grid_size // 2

        # Calculate offsets to center the level
        total_level_width = self.width * self.grid_size
        total_level_height = self.height * self.grid_size
        self.offset_x = (aj.window_width - total_level_width) // 2
        self.offset_y = (aj.window_height - total_level_height) // 2

        if player_pos:
            self.player = Player(
                radius=self.half_grid_size * 0.6,
                x=player_pos[0],
                y=player_pos[1],
            )

        assert self.player is not None, f"No player found in level {self._index}"

    def _clear_level(self) -> None:
        for wall in self.walls.values():
            aj.instance_destroy(wall)
        for crate in self.crates.values():
            aj.instance_destroy(crate)
        for goal in self.goals.values():
            aj.instance_destroy(goal)
        if self.player:
            aj.instance_destroy(self.player)

    def restart(self) -> None:
        self._clear_level()
        self._load_level()

    def next_level(self) -> bool:
        if self._index < self._max_level:
            self._index += 1
            self._load_level()
            return True
        return False

    def previous_level(self) -> bool:
        if self._index > 1:
            self._index -= 1
            self._load_level()
            return True
        return False

    def get_level_info(self) -> str:
        return f"Level {self._index}/{self._max_level}"

    def check_completion(self) -> None:
        if all((int(crate.x), int(crate.y)) in self.goals for crate in self.crates.values()):
            print(f"Level {self._index} completed!")
            if self.next_level():
                print(f"Moving to {self.get_level_info()}")
            else:
                print("Congratulations! You've completed all levels!")
                print("Press R to restart from level 1")
                self._index = 1
                self._load_level()


aj.room_set_caption("Sokoban")
aj.room_set_background(aj.c_purple)
aj.register_objects(Player, Wall, Goal, Crate)

levels_file = Path(__file__).parent / "levels.txt"
level = Level(levels_file)

print("Controls:")
print("Arrow keys: Move")
print("R: Restart current level")
print("N: Next level (skip)")
print("P: Previous level")
print(f"Starting {level.get_level_info()}")

aj.game_start()
