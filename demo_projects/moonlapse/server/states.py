from __future__ import annotations
import logging
from typing import ClassVar, override

from datetime import datetime, timezone
from demo_projects.moonlapse.shared.packets import serverbound, clientbound
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.hub import HubLike
from demo_projects.moonlapse.server.state import State

log = logging.getLogger("moonlapse.states")


class ConnectedState(State):
    NAME: ClassVar[str] = "connected"

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub

    @override
    async def on_enter(self) -> None:
        cid = self.client.id
        await self.hub.send_to(cid, clientbound.ClientId(cid))

        log.info(
            f"connected {cid} as {self.client.ws.remote_address}, total={len(self.hub.get_clients())}"  # pyright: ignore[reportAny]
        )

        server_time = datetime.now(timezone.utc).isoformat()
        motd_text = (
            f"Welcome to Moonlapse!\n"
            f"Server time: {server_time}\n"
            f"Type /login <user> <pass> to enter."
        )
        await self.hub.send_to(cid, clientbound.Motd(motd_text))

    @override
    async def on_exit(self) -> None:
        pass

    @override
    async def handle_packet(
        self, packet: serverbound.ServerboundPacket
    ) -> State | None:
        cid = self.client.id
        if isinstance(packet, serverbound.LoginRequest):
            log.info(f"login from {cid}")
            await self.hub.send_to(cid, clientbound.LoginResponse(ok=True))
            await self.hub.broadcast(
                clientbound.Announcement(f"Player {cid} joined the game."),
                except_for=cid,
            )
            return InGameState(self.client, self.hub)

        elif isinstance(packet, serverbound.RegisterRequest):
            log.info(f"register from {cid}")
            await self.hub.send_to(cid, clientbound.RegisterResponse(ok=True))
            return None

        # Reject everything else
        name = type(packet).__name__
        log.info(f"reject {cid}: {name} in {self.NAME}")
        await self.hub.send_to(
            cid,
            clientbound.ChatResponse(
                ok=False, err=f"'{name}' not allowed while connected"
            ),
        )
        return None


class InGameState(State):
    NAME: ClassVar[str] = "in_game"

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub

    @override
    async def on_enter(self) -> None:
        cid = self.client.id
        await self.hub.broadcast(
            clientbound.Announcement(f"Player {cid} joined the game."),
            except_for=cid,
        )

    @override
    async def on_exit(self) -> None:
        pass

    @override
    async def handle_packet(
        self, packet: serverbound.ServerboundPacket
    ) -> State | None:
        cid = self.client.id
        if isinstance(packet, serverbound.ChatRequest):
            log.info(f"chat from {cid}: {packet.message}")
            await self.hub.send_to(cid, clientbound.ChatResponse(ok=True))
            await self._broadcast_chat(cid, packet.message)
            return None

        elif isinstance(packet, serverbound.MoveRequest):
            log.info(f"move from {cid}: ({packet.dx},{packet.dy})")
            await self.hub.send_to(cid, clientbound.MoveResponse(ok=True))
            return None

        elif isinstance(packet, serverbound.LogoutRequest):
            log.info(f"log out from {cid}")
            await self.hub.send_to(cid, clientbound.LogoutResponse(ok=True))
            return ConnectedState(self.client, self.hub)

        # Reject everything else
        name = type(packet).__name__
        log.info(f"reject {cid}: {name} in {self.NAME}")
        await self.hub.send_to(
            cid,
            clientbound.ChatResponse(
                ok=False, err=f"'{name}' not allowed while in game"
            ),
        )
        return None

    async def _broadcast_chat(self, from_id: int, message: str) -> None:
        """Broadcast chat only to clients in InGameState."""
        for client in self.hub.get_clients():
            if isinstance(client.state, InGameState):
                await self.hub.send_to(
                    client.id, clientbound.PlayerChat(from_id, message)
                )
