"""Chess multiplayer server.

Manages: connections, lobby matchmaking, authoritative game state.
Chess rules come from shared/chess.py — no duplication.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import logging

import websockets
from websockets.asyncio.server import ServerConnection

from demo_projects.chessmultiplayer.shared.chess import (
    BoardState,
    Role,
    Move,
    initial_board,
    is_check,
)
from demo_projects.chessmultiplayer.shared.packets import (
    AssignId,
    BoardStateWire,
    ClientConnected,
    ClientDisconnected,
    GameOver,
    GameStart,
    Join,
    LobbyStatus,
    LobbyUpdate,
    MoveRequest,
    MoveResult,
    Packet,
    decode,
)

log = logging.getLogger("chess_server")


# ── Game model ──────────────────────────────────────────────────────────────


@dataclass
class Game:
    """Server-side game session."""

    id: UUID
    white_id: UUID
    black_id: UUID
    current_turn: Role = Role.white
    state: BoardState = field(default_factory=lambda: initial_board())
    status: str = "playing"
    winner: str = ""


# ── Server state ────────────────────────────────────────────────────────────


@dataclass
class ServerState:
    """Mutable server state — accessed concurrently by WebSocket handlers."""

    games: dict[UUID, Game] = field(default_factory=dict)
    ws_to_id: dict[ServerConnection, UUID] = field(default_factory=dict)
    id_to_ws: dict[UUID, ServerConnection] = field(default_factory=dict)
    client_games: dict[UUID, UUID] = field(default_factory=dict)
    waitlist: deque[UUID] = field(default_factory=deque)


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _send(ws: ServerConnection, packet: Packet) -> None:
    try:
        await ws.send(packet.encode())
    except websockets.exceptions.ConnectionClosed:
        pass


async def _send_to(server: ServerState, client_id: UUID, packet: Packet) -> None:
    ws = server.id_to_ws.get(client_id)
    if ws is not None:
        await _send(ws, packet)


async def _broadcast(server: ServerState, packet: Packet, *, exclude: UUID | None = None) -> None:
    for client_id, ws in list(server.id_to_ws.items()):
        if client_id == exclude:
            continue
        try:
            await _send(ws, packet)
        except websockets.exceptions.ConnectionClosed:
            pass


def _board_to_wire(state: BoardState) -> bytes:
    """Encode board into 64 bytes for the wire protocol."""
    grid_bytes = bytearray(64)
    for row in range(8):
        for col in range(8):
            cell = state.get(col, row)
            if cell is not None:
                grid_bytes[row * 8 + col] = (cell.piece_type.value << 4) | cell.colour.value
            else:
                grid_bytes[row * 8 + col] = 0
    return bytes(grid_bytes)


# ── Lobby & matchmaking ────────────────────────────────────────────────────


async def _register_client(server: ServerState, ws: ServerConnection) -> UUID:
    """Register a new client connection. Returns the new client_id."""
    client_id = uuid4()
    server.ws_to_id[ws] = client_id
    server.id_to_ws[client_id] = ws
    server.client_games[client_id] = uuid4()  # sentinel
    await _send(ws, AssignId(sender_id=client_id))
    await _broadcast(server, ClientConnected(client_id=client_id))
    await _send(ws, LobbyUpdate(status=LobbyStatus.WAITING))
    return client_id


async def _start_game_if_ready(server: ServerState) -> None:
    """If two players are waiting, create a game and notify both."""
    if len(server.waitlist) < 2:
        return
    white_id = server.waitlist.popleft()
    black_id = server.waitlist.popleft()
    game_id = uuid4()
    game = Game(id=game_id, white_id=white_id, black_id=black_id)
    server.games[game_id] = game
    server.client_games[white_id] = game_id
    server.client_games[black_id] = game_id

    for target_id in (white_id, black_id):
        target_ws = server.id_to_ws.get(target_id)
        if target_ws is not None:
            await _send(
                target_ws,
                LobbyUpdate(
                    status=LobbyStatus.MATCH_FOUND,
                    white_id=white_id,
                    black_id=black_id,
                ),
            )
            await _send(
                target_ws,
                GameStart(
                    white_id=white_id,
                    black_id=black_id,
                ),
            )
            await _send(
                target_ws,
                BoardStateWire(
                    grid=_board_to_wire(game.state),
                    next_turn=game.current_turn,
                ),
            )


async def _handle_join(server: ServerState, ws: ServerConnection) -> None:
    """Register client and attempt to start a game."""
    client_id = await _register_client(server, ws)
    server.waitlist.append(client_id)
    await _start_game_if_ready(server)


# ── Move handling ───────────────────────────────────────────────────────────


async def _handle_move(server: ServerState, client_id: UUID, request: MoveRequest) -> None:
    """Validate and apply a move. Authoritative server logic."""
    game_id = server.client_games.get(client_id)
    if game_id is None or game_id not in server.games:
        return
    game = server.games[game_id]
    if game.state.is_finished:
        await _send_to(server, client_id, MoveResult(success=False, error="game over"))
        return

    # Check sender is the current player
    if (game.white_id == client_id and game.current_turn != Role.white) or (
        game.black_id == client_id and game.current_turn != Role.black
    ):
        await _send_to(server, client_id, MoveResult(success=False, error="not your turn"))
        return

    move = Move(
        from_col=request.from_col,
        from_row=request.from_row,
        to_col=request.to_col,
        to_row=request.to_row,
    )
    if not game.state.is_legal(move):
        await _send_to(server, client_id, MoveResult(success=False, error="out of bounds"))
        return

    from_cell = game.state.get(request.from_col, request.from_row)
    if from_cell is None or from_cell.colour != game.current_turn:
        await _send_to(server, client_id, MoveResult(success=False, error="not your piece"))
        return

    legal = game.state.legal_moves(request.from_col, request.from_row)
    if not any(
        m.from_col == request.from_col
        and m.from_row == request.from_row
        and m.to_col == request.to_col
        and m.to_row == request.to_row
        for m in legal
    ):
        await _send_to(server, client_id, MoveResult(success=False, error="invalid move"))
        return

    # Apply move
    game.state = game.state.apply(move)
    game.current_turn = game.current_turn.opposite

    # Check game status
    winner = game.state.check_winner()
    if winner is not None:
        game.status = "finished"
        game.winner = winner.name_title
        for target_id in (game.white_id, game.black_id):
            target_ws = server.id_to_ws.get(target_id)
            if target_ws is not None:
                await _send(
                    target_ws,
                    BoardStateWire(
                        grid=_board_to_wire(game.state),
                        next_turn=game.current_turn,
                    ),
                )
                await _send(
                    target_ws,
                    GameOver(
                        winner=winner,
                        reason="checkmate",
                    ),
                )
        log.info("Game over: %s wins", game.winner)
        return
    elif is_check(game.state, game.current_turn):
        for target_id in (game.white_id, game.black_id):
            target_ws = server.id_to_ws.get(target_id)
            if target_ws is not None:
                await _send(
                    target_ws,
                    BoardStateWire(
                        grid=_board_to_wire(game.state),
                        next_turn=game.current_turn,
                    ),
                )
        await _send_to(server, client_id, MoveResult(success=True))
    else:
        for target_id in (game.white_id, game.black_id):
            target_ws = server.id_to_ws.get(target_id)
            if target_ws is not None:
                await _send(
                    target_ws,
                    BoardStateWire(
                        grid=_board_to_wire(game.state),
                        next_turn=game.current_turn,
                    ),
                )
        await _send_to(server, client_id, MoveResult(success=True))


# ── Disconnect handling ─────────────────────────────────────────────────────


async def _handle_disconnect(server: ServerState, ws: ServerConnection) -> None:
    """Clean up after a client disconnects."""
    client_id = server.ws_to_id.pop(ws, None)
    if client_id is None:
        return
    _ = server.id_to_ws.pop(client_id, None)
    # Also clean up from waitlist if still waiting
    if client_id in server.waitlist:
        server.waitlist.remove(client_id)
    await _broadcast(server, ClientDisconnected(client_id=client_id))

    game_id = server.client_games.pop(client_id, None)
    if game_id is None or game_id not in server.games:
        return

    game = server.games[game_id]

    # Determine which player left
    if game.white_id == client_id:
        survivor_id = game.black_id
    elif game.black_id == client_id:
        survivor_id = game.white_id
    else:
        game.status = "abandoned"
        del server.games[game_id]
        return

    # Notify survivor
    if server.id_to_ws.get(survivor_id) is not None:
        await _send_to(
            server,
            survivor_id,
            MoveResult(
                success=False,
                error=f"opponent {client_id.hex[:8]} disconnected",
            ),
        )
        await _send_to(server, survivor_id, LobbyUpdate(status=LobbyStatus.OPPONENT_LEFT))

    del server.games[game_id]


# ── Main loop ───────────────────────────────────────────────────────────────


async def handle_client(server: ServerState, ws: ServerConnection) -> None:
    try:
        await _handle_join(server, ws)
        async for raw in ws:
            data: bytes = raw if isinstance(raw, bytes) else raw.encode()
            pkt = decode(data)
            if pkt is None:
                continue
            if isinstance(pkt, Join):
                new_id = await _register_client(server, ws)
                server.waitlist.append(new_id)
                await _start_game_if_ready(server)
            elif isinstance(pkt, MoveRequest):
                client_id = server.ws_to_id.get(ws)
                if client_id:
                    await _handle_move(server, client_id, pkt)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await _handle_disconnect(server, ws)


async def main() -> None:
    server = ServerState()
    async with websockets.serve(lambda ws: handle_client(server, ws), host="localhost", port=8766):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
