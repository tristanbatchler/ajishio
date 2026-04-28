from __future__ import annotations

import asyncio
from dataclasses import dataclass
from random import randrange
from uuid import UUID, uuid4

import websockets
from websockets.asyncio.server import ServerConnection
from typing import override

import ajishio as aj
import demo_projects.multiplayer.shared as shared
import demo_projects.multiplayer.shared.game_objects as go
import demo_projects.multiplayer.shared.packet as pck


HOST = "0.0.0.0"
PORT = 8765


@dataclass
class PlayerNetstate:
    obj: go.Player
    ws: ServerConnection
    requested_position_sync_timer: float = 0.0


class GameServer(aj.GameObject):
    """Authoritative multiplayer server.

    - Runs game simulation inside Ajishio step()
    - Accepts websocket packets asynchronously
    - Processes packets on main thread during step()
    """

    def __init__(self, x: float = 0, y: float = 0, **_: object) -> None:
        super().__init__(x, y)

        self.players: dict[UUID, PlayerNetstate] = {}
        self.connections: dict[ServerConnection, UUID] = {}

        self.packet_queue: asyncio.Queue[tuple[pck.Packet, ServerConnection]] = asyncio.Queue()

        self.sync_timer: float = 0.0
        self.sync_interval: float = 1.0

        print("SERVER: started")

    # ------------------------------------------------------------------
    # websocket layer
    # ------------------------------------------------------------------

    async def websocket_handler(self, ws: ServerConnection) -> None:
        print("SERVER: websocket connected", ws.remote_address)  # pyright: ignore[reportAny]

        try:
            async for message in ws:
                if isinstance(message, str):
                    raw = message.encode("utf-8")
                else:
                    raw = message

                packet = pck.decode(raw)
                if packet is None:
                    continue

                await self.packet_queue.put((packet, ws))

        except Exception as exc:
            print("SERVER: websocket error:", exc)

        finally:
            self.disconnect_ws(ws)

    def disconnect_ws(self, ws: ServerConnection) -> None:
        player_id = self.connections.pop(ws, None)
        if player_id is None:
            return

        ns = self.players.pop(player_id, None)
        if ns is not None:
            aj.instance_destroy(ns.obj)

        print("SERVER: disconnected", player_id.hex[:8])

        self.broadcast(pck.PlayerDisconnectPacket(player_id))

    async def send_packet(self, packet: pck.Packet, ws: ServerConnection) -> None:
        try:
            await ws.send(packet.pack())
        except Exception:
            self.disconnect_ws(ws)

    def send_now(self, packet: pck.Packet, ws: ServerConnection) -> None:
        _ = asyncio.create_task(self.send_packet(packet, ws))

    def broadcast(self, packet: pck.Packet, exclude: UUID | None = None) -> None:
        for player_id, ns in list(self.players.items()):
            if exclude is not None and player_id == exclude:
                continue
            self.send_now(packet, ns.ws)

    # ------------------------------------------------------------------
    # ajishio loop
    # ------------------------------------------------------------------

    @override
    def step(self) -> None:
        super().step()

        self.process_packets()

        self.sync_timer += aj.delta_time
        if self.sync_timer >= self.sync_interval:
            self.sync_timer %= self.sync_interval
            self.sync_positions()

    def process_packets(self) -> None:
        while not self.packet_queue.empty():
            packet, ws = self.packet_queue.get_nowait()

            if isinstance(packet, pck.ConnectionRequestPacket):
                self.handle_connection_request(ws)

            elif isinstance(packet, pck.PlayerXInputPacket):
                self.handle_player_x_input(packet)

            elif isinstance(packet, pck.PlayerJumpPacket):
                self.handle_player_jump(packet)

            elif isinstance(packet, pck.PlayerDisconnectPacket):
                self.handle_player_disconnect(packet.player_id)

            elif isinstance(packet, pck.PositionSyncResponsePacket):
                self.handle_position_sync_response(packet)

    # ------------------------------------------------------------------
    # connection / spawning
    # ------------------------------------------------------------------

    def handle_connection_request(self, ws: ServerConnection) -> None:
        if ws in self.connections:
            return

        num_spawners = aj.instance_count(go.PlayerSpawner)
        spawner = aj.instance_find(
            go.PlayerSpawner,
            randrange(num_spawners),
        )
        assert spawner is not None

        player = go.Player(spawner.x, spawner.y)
        player_id = uuid4()
        player.name = player_id.hex[:4]

        self.players[player_id] = PlayerNetstate(player, ws)
        self.connections[ws] = player_id

        print("SERVER: joined", player_id.hex[:8])

        # tell new client its id
        self.send_now(pck.PlayerIdPacket(player_id), ws)

        # tell new client own spawn position
        self.send_now(
            pck.PlayerPositionPacket(player.x, player.y),
            ws,
        )

        # tell new client all existing players
        for other_id, ns in self.players.items():
            if other_id == player_id:
                continue

            self.send_now(
                pck.OtherPlayerPositionPacket(
                    other_id,
                    ns.obj.x,
                    ns.obj.y,
                ),
                ws,
            )

        # tell everyone else about new player
        self.broadcast(
            pck.OtherPlayerPositionPacket(
                player_id,
                player.x,
                player.y,
            ),
            exclude=player_id,
        )

    # ------------------------------------------------------------------
    # gameplay packets
    # ------------------------------------------------------------------

    def handle_player_x_input(
        self,
        packet: pck.PlayerXInputPacket,
    ) -> None:
        ns = self.players.get(packet.player_id)
        if ns is None:
            return

        ns.obj.input_x = packet.x_input
        self.broadcast(packet, exclude=packet.player_id)

    def handle_player_jump(
        self,
        packet: pck.PlayerJumpPacket,
    ) -> None:
        ns = self.players.get(packet.player_id)
        if ns is None:
            return

        ns.obj.jump()
        self.broadcast(packet, exclude=packet.player_id)

    def handle_player_disconnect(self, player_id: UUID) -> None:
        ns = self.players.pop(player_id, None)
        if ns is None:
            return

        self.connections.pop(ns.ws, None)
        aj.instance_destroy(ns.obj)

        print("SERVER: player quit", player_id.hex[:8])

        self.broadcast(pck.PlayerDisconnectPacket(player_id))

    # ------------------------------------------------------------------
    # anti-cheat sync
    # ------------------------------------------------------------------

    def sync_positions(self) -> None:
        for player_id, ns in list(self.players.items()):
            if ns.requested_position_sync_timer >= 5:
                print("SERVER: timeout", player_id.hex[:8])
                self.handle_player_disconnect(player_id)
                continue

            ns.requested_position_sync_timer += 1
            self.send_now(pck.PositionSyncRequestPacket(), ns.ws)

    def handle_position_sync_response(
        self,
        packet: pck.PositionSyncResponsePacket,
    ) -> None:
        ns = self.players.get(packet.player_id)
        if ns is None:
            return

        distance = aj.point_distance(
            ns.obj.x,
            ns.obj.y,
            packet.x,
            packet.y,
        )

        if distance < 10:
            ns.obj.x = packet.x
            ns.obj.y = packet.y
            ns.requested_position_sync_timer = 0

            self.broadcast(
                pck.OtherPlayerPositionPacket(
                    packet.player_id,
                    packet.x,
                    packet.y,
                ),
                exclude=packet.player_id,
            )

        else:
            self.send_now(
                pck.PlayerPositionPacket(
                    ns.obj.x,
                    ns.obj.y,
                ),
                ns.ws,
            )


async def main() -> None:
    aj.set_rooms(shared.rooms)

    # Register only objects that can be spawned from the room data.
    # GameServer is created manually below because the websocket server
    # needs a direct reference to the same instance Ajishio steps.
    aj.register_objects(go.Floor, go.PlayerSpawner)

    aj.room_set_caption("Multiplayer Server")
    aj.room_set_size(shared.room_width, shared.room_height)
    aj.window_set_size(shared.room_width * 2, shared.room_height * 2)
    aj.view_set_wport(aj.view_current, shared.room_width)
    aj.view_set_hport(aj.view_current, shared.room_height)
    aj.room_set_background(shared.room_background_color)

    server = GameServer()

    async with websockets.serve(server.websocket_handler, HOST, PORT):
        print(f"SERVER: listening on {HOST}:{PORT}")
        await aj.async_game_start()


asyncio.run(main())
