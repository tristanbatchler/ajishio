from __future__ import annotations

import asyncio
import logging
from typing import ClassVar, override
from base64 import b64encode

from datetime import datetime, timedelta, timezone

from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.db import query
from demo_projects.moonlapse.server.hub import HubLike
from demo_projects.moonlapse.server.state import State
from demo_projects.moonlapse.shared.entities import Actor, Entity, EntityType
from demo_projects.moonlapse.shared.packets import clientbound, serverbound

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

log = logging.getLogger("moonlapse.states")

sb = serverbound
cb = clientbound


class ConnectedState(State):
    NAME: ClassVar[str] = "connected"
    PASSWORD_HASHER: ClassVar[PasswordHasher] = PasswordHasher()

    def __init__(self, client: Client, hub: HubLike) -> None:
        self.client: Client = client
        self.hub: HubLike = hub
        self.cid: int = self.client.id

    @override
    async def on_enter(self) -> None:
        cid = self.client.id
        await self.hub.send_client_ws(cid, cb.ClientId(cid))
        log.info(
            f"connected {cid} as {self.client.ip_address}, total={len(self.hub.get_clients())}"
        )
        server_time = datetime.now(timezone.utc).isoformat()
        motd_text = (
            "Welcome to Moonlapse!\n"
            f"Server time: {server_time}\n"
            "Type /login <user> <pass> to enter."
        )
        await self.hub.send_client_ws(cid, cb.Motd(motd_text))

    @override
    async def on_exit(self) -> None:
        pass

    async def _handle_login_request(self, p: sb.LoginRequest):
        log.info("login from %s: %s", self.cid, p.username)

        lockout_period_minutes = 15
        lockout_max_attempts = 5

        user = await query.get_user_by_username(self.hub.db_conn, username=p.username)
        if user is None:
            await self.hub.send_client_ws(
                self.cid, cb.LoginResponse(ok=False, err="User not found")
            )
            return None

        active_lockouts = await query.get_active_user_lockouts_by_user_id(
            self.hub.db_conn, user_id=user.id_
        )
        if active_lockouts:
            lockout = active_lockouts[0]
            await self.hub.send_client_ws(
                self.cid,
                cb.LoginResponse(
                    ok=False,
                    err=(
                        "Account locked due to too many failed login "
                        "attempts. Please try again later."
                    ),
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
            _ = self.PASSWORD_HASHER.verify(user.password_hash, p.password)
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
                ip_address=self.client.ip_address,
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
                        err=(
                            "Account locked due to too many failed login "
                            "attempts. Please try again later."
                        ),
                    ),
                )
            else:
                await self.hub.send_client_ws(
                    self.cid, cb.LoginResponse(ok=False, err="Incorrect password")
                )
            return None

        await self.hub.send_client_ws(self.cid, cb.LoginResponse(ok=True))
        _ = await query.create_user_login(
            self.hub.db_conn,
            user_id=user.id_,
            ip_address=self.client.ip_address,
        )
        await self.hub.db_conn.commit()

        actor_entity = await query.get_actor_by_user_id(
            self.hub.db_conn, user_id=user.id_
        )
        if actor_entity is None:
            await self.hub.send_client_ws(
                self.cid,
                cb.ServerError(
                    "Login succeeded, but no player information was found. Please contact support."
                ),
            )
            return

        new_state = InGameState(
            self.client,
            self.hub,
            Actor(
                entity_id=self.hub.next_entity_id,
                name=actor_entity.entity_name,
                x=actor_entity.x_position,
                y=actor_entity.y_position,
            ),
        )

        return new_state

    async def _handle_register_request(self, p: sb.RegisterRequest) -> State | None:
        log.info("register from %s: %s", self.cid, p.username)
        user = await query.get_user_by_username(self.hub.db_conn, username=p.username)
        if user is not None:
            await self.hub.send_client_ws(
                self.cid, cb.RegisterResponse(ok=False, err="User already exists")
            )
            return

        pw_hash = self.PASSWORD_HASHER.hash(p.password)
        user = await query.create_user(
            self.hub.db_conn, username=p.username, password_hash=pw_hash
        )
        if user is None:
            await self.hub.send_client_ws(
                self.cid,
                cb.RegisterResponse(
                    ok=False,
                    err="Registration failed due to an unknown error. Please contact support",
                ),
            )
            return

        entity = await query.create_entity(
            self.hub.db_conn,
            entity_type=EntityType.ACTOR,
            entity_name=p.username,
            x_position=0,
            y_position=0,
        )
        if entity is None:
            await self.hub.send_client_ws(
                self.cid,
                cb.ServerError(
                    "Registration succeeded, but was unable to create player. Please contact support."
                ),
            )
            return

        _ = await query.create_actor(
            self.hub.db_conn, entity_id=entity.id_, user_id=user.id_
        )
        await self.hub.db_conn.commit()
        await self.hub.send_client_ws(self.cid, cb.RegisterResponse(ok=True))

    @override
    async def handle_packet(self, p: sb.ServerboundPacket) -> State | None:
        match p:
            case sb.LoginRequest():
                return await self._handle_login_request(p)
            case sb.RegisterRequest():
                return await self._handle_register_request(p)
            case _:
                log.info("reject %s: %s in %s", self.cid, p.TYPE, self.NAME)
                await self.hub.send_client_ws(
                    self.cid, cb.ServerError("You can't do that here")
                )
                return None


class InGameState(State):
    NAME: ClassVar[str] = "in_game"

    def __init__(self, client: Client, hub: HubLike, actor: Actor) -> None:
        self.client: Client = client
        self.hub: HubLike = hub
        self.cid: int = self.client.id
        self.actor: Actor = actor
        self._actor_position_db_sync_task: asyncio.Task[None] | None = None

    @staticmethod
    def _serialize_entity_details(entity: Entity) -> str:
        return b64encode(cb.EntityDetails.from_entity(entity).to_bytes()).decode()

    @override
    async def on_enter(self) -> None:
        await self.hub.send_client_ws(
            self.cid, cb.Announcement(f"{self.actor.name} joined the game.")
        )
        log.info(f"{self.actor.name} entered in-game state.")
        # Broadcast this player's spawn to everyone
        await self.hub.broadcast(
            cb.EntitySpawn(
                self.actor.entity_id,
                entity_type=self.actor.TYPE,
                entity_details_blob=self._serialize_entity_details(self.actor),
            )
        )

        self._actor_position_db_sync_task = asyncio.create_task(
            self._sync_db_actor_position_loop()
        )
        self._actor_position_db_sync_task.add_done_callback(
            lambda t: log.warning("position sync task died: %s", t.exception()) if t.exception() else None
        )

        # Send them all the entities in the world
        for entity in self.hub.world.entities.values():
            details = self._serialize_entity_details(entity)
            await self.hub.send_client_ws(
                self.cid, cb.EntitySpawn(entity.entity_id, entity.TYPE, details)
            )

        # Add us to the world
        self.hub.world.spawn_entity(self.actor)

    @override
    async def on_exit(self) -> None:
        self.hub.world.destroy_entity(self.actor.entity_id)
        await self._sync_db_actor_position()
        if self._actor_position_db_sync_task:
            _ = self._actor_position_db_sync_task.cancel()
            try:
                await self._actor_position_db_sync_task
            except asyncio.CancelledError:
                pass
        await self.hub.send_client_ws(
            self.cid, cb.Announcement(f"{self.actor.name} left the game.")
        )
        log.info(f"{self.actor.name} exited in-game state.")
        # Broadcast this player's destroy to everyone
        await self.hub.broadcast(cb.EntityDestroy(entity_id=self.actor.entity_id))

    async def _sync_db_actor_position(self):
    
        _ = await query.update_entity_position(
            self.hub.db_conn,
            x_position=int(self.actor.x),
            y_position=int(self.actor.y),
            id_=self.actor.entity_id,
        )
        await self.hub.db_conn.commit()

    async def _sync_db_actor_position_loop(self):
        try:
            while True:
                await asyncio.sleep(5)
                await self._sync_db_actor_position()
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("position sync loop failed")

    async def _handle_chat_request(self, p: sb.ChatRequest) -> None:
        log.info("chat from %s: %s", self.cid, p.message)
        await self.hub.send_client_ws(self.cid, cb.ChatResponse(ok=True))
        await self.hub.broadcast(
            cb.PlayerChat(self.cid, p.message),
            only_to={
                c.id for c in self.hub.get_clients() if isinstance(c.state, InGameState)
            },
        )

    async def _handle_move_request(self, p: sb.MoveRequest) -> None:
        log.info(
            f"move from {self.cid}: ({self.actor.x},{self.actor.y}) → ({p.dx},{p.dy})"
        )
        self.actor.x += p.dx
        self.actor.y += p.dy
        # Broadcast position to everyone (including self)
        await self.hub.broadcast(
            cb.EntityUpdate(
                self.actor.entity_id,
                entity_details_blob=self._serialize_entity_details(self.actor),
            ),
            only_to={
                c.id for c in self.hub.get_clients() if isinstance(c.state, InGameState)
            },
        )
        await self.hub.send_client_ws(self.cid, cb.MoveResponse(ok=True))

    async def _handle_logout_request(self, p: sb.LogoutRequest) -> State | None:
        log.info("log out from %s: %s", self.cid, p)
        await self.hub.send_client_ws(self.cid, cb.LogoutResponse(ok=True))
        return ConnectedState(self.client, self.hub)

    @override
    async def handle_packet(self, p: sb.ServerboundPacket) -> State | None:
        log.debug("InGameState got packet: %s", type(p).__name__)
        match p:
            case sb.ChatRequest():
                return await self._handle_chat_request(p)
            case sb.MoveRequest():
                return await self._handle_move_request(p)
            case sb.LogoutRequest():
                return await self._handle_logout_request(p)
            case _:
                log.info(f"reject {self.cid}: {type(p).__name__} in self.NAME")
                await self.hub.send_client_ws(
                    self.cid, cb.ServerError("You can't do that here")
                )
