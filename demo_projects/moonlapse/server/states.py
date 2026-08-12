from __future__ import annotations
import logging
from typing import ClassVar, override

from datetime import datetime, timedelta, timezone
from demo_projects.moonlapse.shared.packets import serverbound, clientbound
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.db import query
from demo_projects.moonlapse.server.hub import HubLike
from demo_projects.moonlapse.server.state import State
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


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

        self.ph: PasswordHasher = PasswordHasher()

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

        lockout_period_minutes = 15
        lockout_max_attempts = 5

        user = await query.get_user_by_username(
            self.hub.db_conn,
            username=p.username,
        )
        if user is None:
            await self.hub.send_client_ws(
                self.cid,
                cb.LoginResponse(ok=False, err="User not found"),
            )
            return None

        # Check for an existing lockout first of all
        active_lockouts = await query.get_active_user_lockouts_by_user_id(
            self.hub.db_conn,
            user_id=user.id_,
        )
        if active_lockouts:
            lockout = active_lockouts[0]
            await self.hub.send_client_ws(
                self.cid,
                cb.LoginResponse(
                    ok=False,
                    err="Account locked due to too many failed login attempts. Please try again later.",
                ),
            )
            log.info(
                "login rejected due to lockout: %s (id=%d), expiration=%s",
                user.username,
                user.id_,
                lockout.expiration,
            )
            return None

        try:
            _ = self.ph.verify(user.password_hash, p.password)

        except VerifyMismatchError:
            log.info(
                "login fail %d: user=%s (id=%d)",
                self.cid,
                user.username,
                user.id_,
            )

            _ = await query.create_user_login_failure(
                self.hub.db_conn,
                user_id=user.id_,
                ip_address=self.client.ws.remote_address[0],  # pyright: ignore[reportAny]
            )
            await self.hub.db_conn.commit()

            since_time = datetime.now(tz=timezone.utc) - timedelta(
                minutes=lockout_period_minutes
            )
            failure_count = await query.count_user_login_failures_by_user_id_since(
                self.hub.db_conn,
                user_id=user.id_,
                added=since_time,
            )

            log.info(
                "lockout check %d: user=%s failure_count=%s",
                self.cid,
                user.username,
                failure_count,
            )

            if failure_count is not None and failure_count >= lockout_max_attempts:
                expiration_time = datetime.now(tz=timezone.utc) + timedelta(
                    minutes=lockout_period_minutes
                )

                _ = await query.create_user_lockout(
                    self.hub.db_conn,
                    user_id=user.id_,
                    expiration=expiration_time,
                )
                await self.hub.db_conn.commit()

                log.info(
                    "LOCKING OUT user %s (%d failures) until %s",
                    user.username,
                    failure_count,
                    expiration_time.isoformat(),
                )

                await self.hub.send_client_ws(
                    self.cid,
                    cb.LoginResponse(
                        ok=False,
                        err="Account locked due to too many failed login attempts. Please try again later.",
                    ),
                )
            else:
                await self.hub.send_client_ws(
                    self.cid,
                    cb.LoginResponse(ok=False, err="Incorrect password"),
                )

            return None

        await self.hub.send_client_ws(
            self.cid,
            cb.LoginResponse(ok=True),
        )

        _ = await query.create_user_login(
            self.hub.db_conn,
            user_id=user.id_,
            ip_address=self.client.ws.remote_address[0],  # pyright: ignore[reportAny]
        )
        await self.hub.db_conn.commit()

        return InGameState(self.client, self.hub)

    async def _handle_register_request(self, p: sb.RegisterRequest) -> State | None:
        log.info(f"register from {self.cid}: {p}")
        user = await query.get_user_by_username(self.hub.db_conn, username=p.username)
        if user is not None:
            await self.hub.send_client_ws(
                self.cid, cb.RegisterResponse(ok=False, err="User already exists")
            )
            return None

        pw_hash = self.ph.hash(p.password)
        _ = await query.create_user(
            self.hub.db_conn, username=p.username, password_hash=pw_hash
        )
        await self.hub.db_conn.commit()

        await self.hub.send_client_ws(self.cid, cb.RegisterResponse(ok=True))
        return None

    @override
    async def handle_packet(self, p: sb.ServerboundPacket) -> State | None:
        match p:
            case sb.LoginRequest():
                return await self._handle_login_request(p)
            case sb.RegisterRequest():
                return await self._handle_register_request(p)
            case _:
                log.info(f"reject {self.cid}: {p.TYPE} in {self.NAME}")
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
        await self.hub.send_client_ws(
            self.cid, cb.Announcement(f"Player {self.cid} joined the game.")
        )
        log.info(f"{self.cid} entered in-game state.")

    @override
    async def on_exit(self) -> None:
        await self.hub.send_client_ws(
            self.cid, cb.Announcement(f"Player {self.cid} left the game.")
        )
        log.info(f"{self.cid} exited in-game state.")

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
            case _:
                log.info(f"reject {self.cid}: {p.TYPE} in {self.NAME}")
                await self.hub.send_client_ws(
                    self.cid, cb.ServerError("You can't do that here")
                )
                return None
