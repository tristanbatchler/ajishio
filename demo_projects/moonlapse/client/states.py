from __future__ import annotations

import logging
from typing import ClassVar, override

import ajishio as aj

from demo_projects.moonlapse.shared.packets import clientbound, serverbound
from demo_projects.moonlapse.client.protocol import ManagerLike, State

# Convenient aliases
cb = clientbound
sb = serverbound

log = logging.getLogger("moonlapse.states")


class ConnectingState(State):
    NAME: ClassVar[str] = "connecting"

    def __init__(self, manager: ManagerLike):
        self.mgr: ManagerLike = manager

    @override
    def on_enter(self):
        self.mgr.log("Waiting for acknowledgement from the server...", aj.c_ltgray)

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
                self.mgr.log(
                    f"Unexpected while connecting: {type(p).__name__}", aj.c_ltgray
                )

    @override
    def handle_text_input(self, text: str) -> None:
        pass


class ConnectedState(State):
    NAME: ClassVar[str] = "connected"

    def __init__(self, manager: ManagerLike):
        self.mgr: ManagerLike = manager

    @override
    def on_enter(self):
        self.mgr.log("Connected (not logged in).", aj.c_aqua)

    @override
    def on_exit(self):
        pass

    def _handle_login_response(self, p: cb.LoginResponse):
        if not p.ok:
            self.mgr.log(f"Can't login: {p.err}", aj.c_orange)
        else:
            self.mgr.log("Login success", aj.c_lime)
            return InGameState(self.mgr)

    def _handle_register_response(self, p: cb.RegisterResponse):
        if not p.ok:
            self.mgr.log(f"Can't register: {p.err}", aj.c_orange)
        else:
            self.mgr.log("Register success", aj.c_lime)

    def _handle_motd(self, p: cb.Motd):
        self.mgr.log(p.motd, aj.c_aqua)

    def _handle_announcement(self, p: cb.Announcement):
        self.mgr.log(p.message, aj.c_yellow)

    def _handle_client_disconnected(self, p: cb.ClientDisconnected):
        self.mgr.log(f"Player {p.client_id} disconnected", aj.c_yellow)

    @override
    def handle_packet(self, p: clientbound.ClientboundPacket):
        match p:
            case clientbound.LoginResponse():
                return self._handle_login_response(p)
            case clientbound.RegisterResponse():
                return self._handle_register_response(p)
            case clientbound.Motd():
                return self._handle_motd(p)
            case clientbound.Announcement():
                return self._handle_announcement(p)
            case clientbound.ClientDisconnected():
                return self._handle_client_disconnected(p)
            case _:
                self.mgr.log(
                    f"Unexpected while connected: {type(p).__name__}", aj.c_ltgray
                )

    @override
    def handle_text_input(self, text: str):
        parts = text.split()
        if not parts:
            return
        if parts[0] == "/login" and len(parts) >= 3:
            pkt = serverbound.LoginRequest(username=parts[1], password=parts[2])
            self.mgr.client.send(pkt.serialize())
            self.mgr.log(f"Sending login as {parts[1]}", aj.c_lime)
        elif parts[0] == "/who":
            self.mgr.log(f"My ID: {self.mgr.get_client_id()}", aj.c_aqua)
        elif parts[0] == "/register" and len(parts) >= 3:
            pkt = serverbound.RegisterRequest(username=parts[1], password=parts[2])
            self.mgr.client.send(pkt.serialize())
            self.mgr.log("Sending register...", aj.c_yellow)
        else:
            self.mgr.log("Must be logged in to send messages.", aj.c_orange)


class InGameState(State):
    NAME: ClassVar[str] = "in_game"

    def __init__(self, manager: ManagerLike):
        self.mgr: ManagerLike = manager

    @override
    def on_enter(self):
        self.mgr.log("Logged in.", aj.c_lime)

    @override
    def on_exit(self) -> None:
        pass

    def _handle_logout_response(self, p: cb.LogoutResponse):
        if not p.ok:
            self.mgr.log(f"Can't logout: {p.err}", aj.c_orange)
        else:
            self.mgr.log("Logout success", aj.c_lime)
            return ConnectedState(self.mgr)

    def _handle_chat_response(self, p: cb.ChatResponse):
        if not p.ok:
            self.mgr.log(f"Can't send that: {p.err}", aj.c_orange)

    def _handle_move_response(self, p: cb.MoveResponse):
        if not p.ok:
            self.mgr.log(f"Can't move there: {p.err}", aj.c_orange)
        else:
            self.mgr.log("Move successful", aj.c_lime)

    def _handle_announcement(self, p: cb.Announcement):
        self.mgr.log(p.message, aj.c_yellow)

    def _handle_client_disconnected(self, p: cb.ClientDisconnected):
        self.mgr.log(f"Player {p.client_id} disconnected", aj.c_yellow)

    def _handle_player_chat(self, p: cb.PlayerChat):
        self.mgr.log(f"Player {p.from_client_id} says: '{p.message}'", aj.c_white)

    @override
    def handle_packet(self, p: clientbound.ClientboundPacket):
        match p:
            case clientbound.LogoutResponse():
                return self._handle_logout_response(p)
            case clientbound.ChatResponse():
                return self._handle_chat_response(p)
            case clientbound.MoveResponse():
                return self._handle_move_response(p)
            case clientbound.Announcement():
                return self._handle_announcement(p)
            case clientbound.ClientDisconnected():
                return self._handle_client_disconnected(p)
            case clientbound.PlayerChat():
                return self._handle_player_chat(p)
            case _:
                self.mgr.log(f"Unexpected in game: {type(p).__name__}", aj.c_ltgray)

    @override
    def handle_text_input(self, text: str):
        parts = text.split()
        if not parts:
            return
        if parts[0] == "/who":
            self.mgr.log(f"My ID: {self.mgr.get_client_id()}", aj.c_aqua)
        elif parts[0] == "/logout":
            pkt = serverbound.LogoutRequest()
            self.mgr.client.send(pkt.serialize())
            self.mgr.log("Sending logout...", aj.c_yellow)
        else:
            pkt = serverbound.ChatRequest(text)
            self.mgr.client.send(pkt.serialize())
