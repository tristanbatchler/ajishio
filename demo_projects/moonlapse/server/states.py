from __future__ import annotations
import logging
from typing import ClassVar, override

from datetime import datetime, timezone
from demo_projects.moonlapse.shared.packets import serverbound, clientbound
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.hub import HubLike
from demo_projects.moonlapse.server.state import State

log = logging.getLogger("moonlapse.states")


class ConnectingState(State):
    NAME: ClassVar[str] = "connecting"

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
        if isinstance(packet, serverbound.LoginRequest):
            pass
        if isinstance(packet, serverbound.RegisterRequest):
            pass
        return None


class ConnectedState(State):
    NAME: ClassVar[str] = "connected"

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub

    @override
    async def on_enter(self) -> None:
        pass

    @override
    async def on_exit(self) -> None:
        pass

    @override
    async def handle_packet(
        self, packet: serverbound.ServerboundPacket
    ) -> State | None:
        if isinstance(packet, serverbound.LoginRequest):
            pass
        if isinstance(packet, serverbound.RegisterRequest):
            pass


class InGameState(State):
    NAME: ClassVar[str] = "in_game"

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub

    @override
    async def on_enter(self) -> None:
        pass

    @override
    async def on_exit(self) -> None:
        pass

    @override
    async def handle_packet(
        self, packet: serverbound.ServerboundPacket
    ) -> State | None:
        if isinstance(packet, serverbound.ChatRequest):
            pass
        elif isinstance(packet, serverbound.MoveRequest):
            pass
        elif isinstance(packet, serverbound.LogoutRequest):
            pass
        return None
