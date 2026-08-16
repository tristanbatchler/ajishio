from __future__ import annotations
import ajishio as aj

import logging
import string
from typing import ClassVar, Literal, overload, override, Unpack
from base64 import b64decode


from demo_projects.moonlapse.shared import entities
from demo_projects.moonlapse.client.protocol import ManagerLike, State
from demo_projects.moonlapse.shared.constants import GRID_SIZE
from demo_projects.moonlapse.shared.packets import clientbound, serverbound
from demo_projects.moonlapse.client.util import draw_wrapped_text
from demo_projects.moonlapse.shared.world import World


# Convenient aliases
cb = clientbound
sb = serverbound

logger = logging.getLogger("moonlapse.states")


class ConnectingState(aj.GameObject, State):
    NAME: ClassVar[str] = "connecting"

    def __init__(
        self,
        manager: ManagerLike,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.mgr: ManagerLike = manager

    @override
    def on_enter(self):
        logger.info("Waiting for acknowledgement from the server...")

    @override
    def on_exit(self):
        pass

    def _handle_client_id(self, p: cb.ClientId):
        self.mgr.set_client_id(p.id)
        return ConnectedState(self.mgr)

    @override
    def handle_packet(self, p: cb.ClientboundPacket):
        match p:
            case cb.ClientId():
                return self._handle_client_id(p)
            case _:
                logger.error(
                    f"Unexpected while connecting: {type(p).__name__}", aj.c_ltgray
                )


class ConnectedState(aj.GameObject, State):
    NAME: ClassVar[str] = "connected"

    def __init__(
        self,
        manager: ManagerLike,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.mgr: ManagerLike = manager
        self.input_buffer: str = ""
        self.message_log: list[tuple[str, aj.Color]] = []
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.5

    @override
    def on_enter(self):
        self.log("Connected (not logged in).", aj.c_aqua)

    @override
    def on_exit(self):
        pass

    def _handle_login_response(self, p: cb.LoginResponse):
        if not p.ok:
            self.log(f"Can't login: {p.err}", aj.c_orange)
        else:
            self.log("Login success", aj.c_lime)
            world = World()
            return InGameState(self.mgr, world)

    def _handle_register_response(self, p: cb.RegisterResponse):
        if not p.ok:
            self.log(f"Can't register: {p.err}", aj.c_orange)
        else:
            self.log("Register success", aj.c_lime)

    def _handle_motd(self, p: cb.Motd):
        self.log(p.motd, aj.c_aqua)

    def _handle_announcement(self, p: cb.Announcement):
        self.log(p.message, aj.c_yellow)

    def _handle_client_disconnected(self, p: cb.ClientDisconnected):
        self.log(f"Player {p.client_id} disconnected", aj.c_yellow)

    @override
    def handle_packet(self, p: cb.ClientboundPacket):
        match p:
            case cb.LoginResponse():
                return self._handle_login_response(p)
            case cb.RegisterResponse():
                return self._handle_register_response(p)
            case cb.Motd():
                return self._handle_motd(p)
            case cb.Announcement():
                return self._handle_announcement(p)
            case cb.ClientDisconnected():
                return self._handle_client_disconnected(p)
            case _:
                self.log(f"Unexpected while connected: {type(p).__name__}", aj.c_ltgray)

    def log(self, message: str, color: aj.Color):
        self.message_log.append((message, color))
        logger.info("%s", message)
        if len(self.message_log) > 50:
            self.message_log = self.message_log[-50:]

    def handle_text_input(self, text: str):
        parts = text.split()
        if not parts:
            return
        if parts[0] == "/login" and len(parts) >= 3:
            pkt = sb.LoginRequest(username=parts[1], password=parts[2])
            self.mgr.send(pkt)
            self.log(f"Sending login as {parts[1]}", aj.c_lime)
        elif parts[0] == "/who":
            self.log(f"My ID: {self.mgr.get_client_id()}", aj.c_aqua)
        elif parts[0] == "/register" and len(parts) >= 3:
            pkt = sb.RegisterRequest(username=parts[1], password=parts[2])
            self.mgr.send(pkt)
            self.log("Sending register...", aj.c_yellow)
        else:
            self.log("Must be logged in to send messages.", aj.c_orange)

    @override
    def step(self) -> None:
        for ch in string.printable:
            if aj.keyboard_check_pressed(ord(ch)):
                self.input_buffer += ch

        if aj.keyboard_check_pressed(aj.vk_backspace) and self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

        if aj.keyboard_check_pressed(aj.vk_enter):
            self.handle_text_input(self.input_buffer)
            self.input_buffer = ""

        self.cursor_timer -= aj.delta_time
        if self.cursor_timer <= 0:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.5

    @override
    def draw(self) -> None:
        super().draw()
        title = f"Moonlapse ({self.NAME})"
        aj.draw_text(10, 10, title, aj.c_lime)

        max_msg_y = 50
        visible: list[tuple[str, aj.Color]] = self.message_log[-15:]
        for line, color in visible:
            num_lines = draw_wrapped_text(10, max_msg_y, line, color, max_width=500)
            max_msg_y += num_lines * 24

        cursor = "|" if self.cursor_visible else " "
        aj.draw_text(10, 400, self.input_buffer + cursor)


class InGameState(aj.GameObject, State):
    NAME: ClassVar[str] = "in_game"

    def __init__(
        self,
        manager: ManagerLike,
        world: World,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.mgr: ManagerLike = manager
        self.world: World = world

    @override
    def on_enter(self):
        logger.info("Logged in.")

    @override
    def on_exit(self) -> None:
        aj.instance_destroy(self.world)

    @overload
    @staticmethod
    def _get_from_details_blob(
        entity_type: entities.EntityType,
        entity_details_blob: str,
        details_only: Literal[True],
    ) -> cb.EntityDetails: ...

    @overload
    @staticmethod
    def _get_from_details_blob(
        entity_type: entities.EntityType,
        entity_details_blob: str,
        details_only: Literal[False],
    ) -> entities.Entity: ...

    @staticmethod
    def _get_from_details_blob(
        entity_type: entities.EntityType, entity_details_blob: str, details_only: bool
    ) -> cb.EntityDetails | entities.Entity:
        data = b64decode(entity_details_blob)

        match entity_type:
            case entities.EntityType.ACTOR:
                details = cb.ActorDetails.from_bytes(data)
                return (
                    details
                    if details_only
                    else entities.Actor(
                        entity_id=details.entity_id,
                        name=details.name,
                        x=details.x,
                        y=details.y,
                    )
                )
            case entities.EntityType.TREE:
                details = cb.TreeDetails.from_bytes(data)
                return (
                    details
                    if details_only
                    else entities.Tree(
                        entity_id=details.entity_id,
                        level=details.level,
                        name=details.name,
                        x=details.x,
                        y=details.y,
                    )
                )
            case entities.EntityType.ORE:
                details = cb.OreDetails.from_bytes(data)
                return (
                    details
                    if details_only
                    else entities.Ore(
                        entity_id=details.entity_id,
                        x=details.x,
                        y=details.y,
                        level=details.level,
                        name=details.name,
                    )
                )
            case entities.EntityType.FISH:
                details = cb.FishDetails.from_bytes(data)
                return (
                    details
                    if details_only
                    else entities.Fish(
                        entity_id=details.entity_id,
                        x=details.x,
                        y=details.y,
                        level=details.level,
                        name=details.name,
                    )
                )
            case _:  # pyright: ignore[reportUnnecessaryComparison]
                raise NotImplementedError(
                    f"Entity spawn for type {entity_type} is unhandled"
                )  # pyright: ignore[reportUnreachable]

    def _handle_logout_response(self, p: cb.LogoutResponse):
        if not p.ok:
            logger.warning(f"Can't logout: {p.err}")
        else:
            logger.info("Logout success")
            return ConnectedState(self.mgr)

    def _handle_chat_response(self, p: cb.ChatResponse):
        if not p.ok:
            logger.warning(f"Can't send that: {p.err}")

    def _handle_move_response(self, p: cb.MoveResponse):
        if not p.ok:
            logger.warning(f"Can't move there: {p.err}")
        else:
            logger.info("Move successful")

    def _handle_announcement(self, p: cb.Announcement):
        logger.info(p.message)

    def _handle_client_disconnected(self, p: cb.ClientDisconnected):
        logger.info(f"Player {p.client_id} disconnected")

    def _handle_player_chat(self, p: cb.PlayerChat):
        logger.info(f"Player {p.from_client_id} says: '{p.message}'")

    def _handle_entity_spawn(self, p: cb.EntitySpawn):
        entity = self._get_from_details_blob(
            p.entity_type, p.entity_details_blob, details_only=False
        )
        self.world.spawn_entity(entity)

    def _handle_entity_destroy(self, p: cb.EntityDestroy):
        self.world.destroy_entity(p.entity_id)

    def _handle_entity_update(self, p: cb.EntityUpdate):
        entity = self.world.entities.get(p.entity_id)
        if entity is None:
            logger.error(f"Can't find entity {p.entity_id} in world to update")
            return

        entity_details = self._get_from_details_blob(
            entity.TYPE, p.entity_details_blob, details_only=True
        )
        self.world.update_entity(p.entity_id, entity_details)

    @override
    def handle_packet(self, p: cb.ClientboundPacket):
        match p:
            case cb.LogoutResponse():
                return self._handle_logout_response(p)
            case cb.ChatResponse():
                return self._handle_chat_response(p)
            case cb.MoveResponse():
                return self._handle_move_response(p)
            case cb.Announcement():
                return self._handle_announcement(p)
            case cb.ClientDisconnected():
                return self._handle_client_disconnected(p)
            case cb.PlayerChat():
                return self._handle_player_chat(p)
            case cb.EntitySpawn():
                return self._handle_entity_spawn(p)
            case cb.EntityDestroy():
                return self._handle_entity_destroy(p)
            case cb.EntityUpdate():
                return self._handle_entity_update(p)
            case cb.ServerError():
                logger.error(f"Server error: {p.message}")
            case _:
                logger.warning(f"Unexpected in game: {type(p).__name__}")

    @override
    def step(self) -> None:
        super().step()
        dx = aj.keyboard_check_pressed(aj.vk_right) - aj.keyboard_check_pressed(
            aj.vk_left
        )
        dy = aj.keyboard_check_pressed(aj.vk_down) - aj.keyboard_check_pressed(aj.vk_up)
        if dx == dy == 0:
            return
        self.mgr.send(sb.MoveRequest(dx * GRID_SIZE, dy * GRID_SIZE))
        logger.debug("Sent a move request")
