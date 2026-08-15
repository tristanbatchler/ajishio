from __future__ import annotations

import logging
from pathlib import Path
from typing import Unpack, override
import ajishio as aj

import string

from demo_projects.moonlapse.shared.packets import deserialize_from_server
from demo_projects.moonlapse.shared.packets import serverbound
from demo_projects.moonlapse.client.protocol import State
from demo_projects.moonlapse.client import states
from demo_projects.moonlapse.client.world import World

log = logging.getLogger("moonlapse.manager")


class Manager(aj.GameObject):
    def __init__(
        self,
        client: aj.GameNetClient,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.client: aj.GameNetClient = client
        self.state: State = states.ConnectingState(self)
        self.client_id: int | None = None
        self.world: World | None = None
        self.message_log: list[tuple[str, aj.Color]] = []
        self.input_buffer: str = ""
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.5
        self.font: aj.Font = aj.load_font(
            Path(__file__).parent / "CutiveMono-Regular.ttf", 24
        )

    def log(self, message: str, color: aj.Color):
        self.message_log.append((message, color))
        log.info("%s", message)
        if len(self.message_log) > 50:
            self.message_log = self.message_log[-50:]

    def set_client_id(self, id: int):
        self.client_id = id

    def get_client_id(self):
        return self.client_id

    def enter_world(self) -> None:
        self.world = World()
        aj.add_object(self.world)
        self.log("Entering world.", aj.c_lime)

    def leave_world(self) -> None:
        if self.world is not None:
            # destroy all entities in world
            for _obj in list(self.world.entities.values()):
                aj.instance_destroy(_obj)
            self.world.entities.clear()
            self.world = None

    def _process_network(self) -> None:
        incoming = self.client.recv()
        while incoming is not None:
            p = deserialize_from_server(incoming)
            new_state = self.state.handle_packet(p)
            if new_state is not None:
                self.state.on_exit()
                self.state = new_state
                self.state.on_enter()
            incoming = self.client.recv()

    def _process_input(self) -> None:
        # Movement when not typing
        if not self.input_buffer and self.world is not None:
            dx = 0
            dy = 0
            if aj.keyboard_check_pressed(ord("a")):
                dx = -1
            if aj.keyboard_check_pressed(ord("d")):
                dx = 1
            if aj.keyboard_check_pressed(ord("w")):
                dy = -1
            if aj.keyboard_check_pressed(ord("s")):
                dy = 1
            if dx != 0 or dy != 0:
                pkt = serverbound.EntityMoveRequest(
                    entity_id=self.client_id or 0,
                    dx=dx,
                    dy=dy,
                )
                self.client.send(pkt.serialize())

        for ch in string.printable:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_backspace) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if aj.keyboard_check_pressed(aj.vk_enter) and self.input_buffer.strip():
            text = self.input_buffer.strip()
            self.state.handle_text_input(text)
            self.input_buffer = ""

    @override
    def step(self) -> None:
        super().step()

        self.cursor_timer -= aj.delta_time
        if self.cursor_timer <= 0:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.5

        self._process_network()
        self._process_input()

    @override
    def draw(self) -> None:
        super().draw()
        aj.draw_set_font(self.font)

        title = f"Moonlapse ({self.state.NAME})"
        aj.draw_text(10, 10, title, aj.c_lime)

        max_msg_y = 50
        visible: list[tuple[str, aj.Color]] = self.message_log[-15:]
        for line, color in visible:
            num_lines = _draw_wrapped_text(
                10, max_msg_y, line, color, self.font, max_width=500
            )
            max_msg_y += num_lines * 24

        cursor = "|" if self.cursor_visible else " "
        aj.draw_text(10, 400, self.input_buffer + cursor)


def _draw_wrapped_text(
    x: float,
    y: float,
    text: str,
    color: aj.Color,
    font: aj.Font,
    *,
    max_width: float = 0.0,
    line_height: float = 24.0,
) -> int:
    """Draw text wrapped to max_width. Returns number of lines drawn."""
    aj.draw_set_font(font)
    effective_max = max_width if max_width > 0 else aj.room_width - x - 20
    if effective_max <= 0:
        effective_max = aj.room_width - x - 20
    words = text.split()
    if not words:
        return 0
    lines: list[str] = []
    current_line: list[str] = []
    current_width: float = 0.0
    for word in words:
        word_w = aj.text_width(word) + aj.text_width(" ")
        if current_width + word_w > effective_max and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_w
        else:
            current_line.append(word)
            current_width += word_w
    if current_line:
        lines.append(" ".join(current_line))
    for i, line_text in enumerate(lines):
        aj.draw_text(x, y + i * line_height, line_text, color)
    return len(lines)
