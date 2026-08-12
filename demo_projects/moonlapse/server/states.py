from __future__ import annotations
import logging
from typing import ClassVar, override

from datetime import datetime, timezone
from demo_projects.moonlapse.shared.packets import serverbound, clientbound
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.hub import HubLike
from demo_projects.moonlapse.server.state import State

log = logging.getLogger("moonlapse.states")

# Convenient aliases
sb = serverbound
cb = clientbound


class ConnectedState(State):
    NAME: ClassVar[str] = "connected"

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub

        # Convenient shorthand
        self.cid: int = self.client.id

    @override
    async def on_enter(self) -> None:
        cid = self.client.id
        await self.hub.send_client_ws(cid, clientbound.ClientId(cid))

        log.info(
            f"connected {cid} as {self.client.ws.remote_address}, total={len(self.hub.get_clients())}"  # pyright: ignore[reportAny]
        )

        server_time = datetime.now(timezone.utc).isoformat()
        motd_text = (
            f"Welcome to Moonlapse!\n"
            f"Server time: {server_time}\n"
            f"Type /login <user> <pass> to enter."
        )
        await self.hub.send_client_ws(cid, clientbound.Motd(motd_text))

    @override
    async def on_exit(self) -> None:
        pass

    async def _handle_login_request(self, p: sb.LoginRequest):
        log.info(f"login from {self.cid}: {p}")
        await self.hub.send_client_ws(self.cid, clientbound.LoginResponse(ok=True))
        await self.hub.broadcast(
            clientbound.Announcement(f"Player {self.cid} joined the game."),
            except_for={self.cid},
        )
        return InGameState(self.client, self.hub)

    async def _handle_register_request(self, p: sb.RegisterRequest):
        log.info(f"register from {self.cid}: {p}")
        await self.hub.send_client_ws(self.cid, cb.RegisterResponse(ok=True))
        return None

    @override
    async def handle_packet(self, p: sb.ServerboundPacket) -> State | None:
        match p:
            case sb.LoginRequest():
                return await self._handle_login_request(p)
            case sb.RegisterRequest():
                return await self._handle_register_request(p)
            case t:
                log.info(f"reject {self.cid}: {t} in {self.NAME}")
                await self.hub.send_client_ws(
                    self.cid, cb.ServerError("You can't do that here")
                )
                return None


class InGameState(State):
    NAME: ClassVar[str] = "in_game"

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub
        self.cid: int = self.client.id

    @override
    async def on_enter(self) -> None:
        await self.hub.broadcast(
            cb.Announcement(f"Player {self.cid} joined the game."),
            except_for={self.cid},
        )

    @override
    async def on_exit(self) -> None:
        pass

    async def _handle_chat_request(self, p: sb.ChatRequest) -> None:
        log.info(f"chat from {self.cid}: {p.message}")
        await self.hub.send_client_ws(self.cid, cb.ChatResponse(ok=True))
        await self.hub.broadcast(
            cb.PlayerChat(self.cid, p.message),
            only_to={
                c.id for c in self.hub.get_clients() if isinstance(c.state, InGameState)
            },
        )

    async def _handle_move_request(self, p: sb.MoveRequest) -> None:
        log.info(f"move from {self.cid}: ({p.dx},{p.dy})")
        await self.hub.send_client_ws(self.cid, cb.MoveResponse(ok=True))

    async def _handle_logout_request(self, p: sb.LogoutRequest) -> State | None:
        log.info(f"log out from {self.cid}: {p}")
        await self.hub.send_client_ws(self.cid, cb.LogoutResponse(ok=True))
        return ConnectedState(self.client, self.hub)

    @override
    async def handle_packet(self, p: sb.ServerboundPacket) -> State | None:
        match p:
            case sb.ChatRequest():
                await self._handle_chat_request(p)
                return None
            case sb.MoveRequest():
                await self._handle_move_request(p)
                return None
            case sb.LogoutRequest():
                return await self._handle_logout_request(p)
            case t:
                log.info(f"reject {self.cid}: {t} in {self.NAME}")
                await self.hub.send_client_ws(
                    self.cid, cb.ServerError("You can't do that here")
                )
                return None
