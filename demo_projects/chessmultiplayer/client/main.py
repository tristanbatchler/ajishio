"""Chess multiplayer client — rendering + input + networking.

Imports chess domain from shared/chess.py — no duplication.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Unpack, final, override
import ajishio as aj

from demo_projects.chessmultiplayer.shared.chess import (
    BoardState,
    Role,
    PieceData,
    PieceType,
    GRID_SIZE,
    initial_board,
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
    decode,
)

# ── Constants ──────────────────────────────────────────────────────────────

PANEL_WIDTH: int = 260
WINDOW_SCALE: int = 2
_COLUMN_LABELS: str = "abcdefgh"
_RANK_LABELS: str = "87654321"
_COLUMN_LABELS_FLIPPED: str = "hgfedcba"
_RANK_LABELS_FLIPPED: str = "12345678"


# ── Game model ────────────────────────────────────────────────────────────


@dataclass
class Game:
    state: BoardState
    current_turn: Role
    my_role: Role | None = None
    lobby_status: LobbyStatus = LobbyStatus.CONNECTING
    opponent_left: bool = False
    opponent_id: str | None = None
    message_log: list[tuple[str, aj.Color]] = field(default_factory=list)
    winner: Role | None = None
    selected_col: int | None = None
    selected_row: int | None = None
    drag_col: int | None = None
    drag_row: int | None = None
    drag_x: float = 0.0
    drag_y: float = 0.0

    @property
    def game_over(self) -> bool:
        return self.winner is not None

    def clear_selection(self) -> None:
        self.selected_col = None
        self.selected_row = None
        self.drag_col = None
        self.drag_row = None
        self.drag_x = 0.0
        self.drag_y = 0.0

    def reset(self) -> None:
        self.state = initial_board()
        self.current_turn = Role.white
        self.selected_col = None
        self.selected_row = None
        self.drag_col = None
        self.drag_row = None
        self.drag_x = 0.0
        self.drag_y = 0.0
        self.winner = None
        self.lobby_status = LobbyStatus.PLAYING


# ── Assets ────────────────────────────────────────────────────────────────

_project_dir = Path(__file__).parent
_font_path = _project_dir / "CutiveMono-Regular.ttf"

sprites: aj.GameSprite | None = None
font: aj.Font | None = None
_label_font: aj.Font | None = None
_win_font: aj.Font | None = None
_prompt_font: aj.Font | None = None


def _ensure_assets() -> None:
    global sprites, font, _label_font, _win_font, _prompt_font
    if sprites is not None:
        return
    sprites = aj.load_aseprite_sprite(_project_dir / "sprites")
    font = aj.load_font(_font_path, 20)
    _label_font = aj.load_font(_font_path, 16)
    _win_font = aj.load_font(_font_path, 28)
    _prompt_font = aj.load_font(_font_path, 16)


def _tile_size() -> int:
    if sprites is None:
        return 72
    return sprites.width


def _sprite_size() -> int:
    if sprites is None:
        return 72
    return sprites.width


def _board_size() -> int:
    return GRID_SIZE * _tile_size()


def _room_width() -> int:
    return PANEL_WIDTH + _board_size()


def _room_height() -> int:
    return _board_size()


def _col_x(col: int) -> float:
    return _board_offset_x + col * _tile_size()


def _row_y(row: int) -> float:
    return _board_offset_y + row * _tile_size()


def _frame_index(ptype: PieceType, colour: Role) -> int:
    return (ptype.value - 1) * 2 + colour.value - 1


def _mouse_room_position() -> tuple[float, float]:
    win_w = aj.window_width
    vp_w = aj.view_wport[aj.view_current]
    vp_x = aj.view_xport[aj.view_current]
    scale = vp_w / win_w if win_w > 0 else 1.0
    return (
        (aj.mouse_x - vp_x) * scale,
        (aj.mouse_y - aj.view_yport[aj.view_current]) * scale,
    )


# ── Board rendering helpers ──────────────────────────────────────────────


def _visual_grid_iter(flipped: bool):
    """Yield (col, logical_row) in visual draw order for flipped boards."""
    if flipped:
        for sc in range(GRID_SIZE):
            col = GRID_SIZE - 1 - sc
            for row in range(GRID_SIZE):
                yield col, (GRID_SIZE - 1 - row)
    else:
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                yield col, row


def _cell_at(screen_col: int, screen_row: int, flipped: bool) -> tuple[int, int]:
    """Convert screen coordinates to logical board coordinates."""
    logical_col = (GRID_SIZE - 1 - screen_col) if flipped else screen_col
    logical_row = (GRID_SIZE - 1 - screen_row) if flipped else screen_row
    return logical_col, logical_row


_board_offset_x: float = 0.0
_board_offset_y: float = 0.0


# ── Game objects ──────────────────────────────────────────────────────────


class BoardRenderer(aj.GameObject):
    game: Game

    def __init__(self, game: Game, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(0, 0, **kwargs)
        self.game = game

    @override
    def draw(self) -> None:
        _ensure_assets()
        assert font is not None
        assert _label_font is not None
        self._draw_board_background(font=_label_font)
        self._draw_pieces()
        self._draw_selection()
        self._draw_valid_move_hints()
        self._draw_drag()

    def _draw_board_background(self, *, font: aj.Font) -> None:
        flipped = self.game.my_role == Role.black
        board_sz = _tile_size() * GRID_SIZE
        aj.draw_rectangle(
            _board_offset_x,
            _board_offset_y,
            _board_offset_x + board_sz,
            _board_offset_y + board_sz,
            color=aj.c_black,
        )
        ts = _tile_size()
        for col, logical_row in _visual_grid_iter(flipped):
            x, y = _col_x(col), _row_y(logical_row)
            color = aj.c_ltgray if (col + logical_row) % 2 == 0 else aj.c_dkgray
            aj.draw_rectangle(x, y, x + ts, y + ts, color=color)
        aj.draw_rectangle(
            _board_offset_x,
            _board_offset_y,
            _board_offset_x + board_sz,
            _board_offset_y + board_sz,
            outline=True,
        )
        aj.draw_set_font(font)
        for i in range(GRID_SIZE):
            cx = _col_x(i) + ts - 14
            cy = _row_y(GRID_SIZE - 1) + ts - 22
            labels = _COLUMN_LABELS_FLIPPED if flipped else _COLUMN_LABELS
            aj.draw_text(cx, cy, labels[i], aj.c_white)
            cx = _board_offset_x + 4
            cy = _row_y(i) + 8
            labels = _RANK_LABELS_FLIPPED if flipped else _RANK_LABELS
            aj.draw_text(cx, cy, labels[i], aj.c_white)

    def _draw_pieces(self) -> None:
        assert sprites is not None
        flipped = self.game.my_role == Role.black
        ts = _tile_size()
        ss = _sprite_size()
        for col, logical_row in _visual_grid_iter(flipped):
            vis_col = GRID_SIZE - 1 - col if flipped else col
            vis_row = GRID_SIZE - 1 - logical_row if flipped else logical_row
            cell = self.game.state.get(vis_col, vis_row)
            if cell is None:
                continue
            if self.game.drag_col is not None and self.game.drag_row is not None:
                drag_vis_col = (
                    GRID_SIZE - 1 - self.game.drag_col
                    if flipped
                    else self.game.drag_col
                )
                drag_vis_row = (
                    GRID_SIZE - 1 - self.game.drag_row
                    if flipped
                    else self.game.drag_row
                )
                if col == drag_vis_col and logical_row == drag_vis_row:
                    continue
            px, py = _col_x(col), _row_y(logical_row)
            offset = (ts - ss) // 2
            frame = _frame_index(cell.piece_type, cell.colour)
            aj.draw_sprite(px + offset, py + offset, sprites, frame)

    def _draw_selection(self) -> None:
        sc, sr = self.game.selected_col, self.game.selected_row
        if sc is None or sr is None:
            return
        flipped = self.game.my_role == Role.black
        vis_col = GRID_SIZE - 1 - sc if flipped else sc
        vis_row = GRID_SIZE - 1 - sr if flipped else sr
        sx, sy = _col_x(vis_col), _row_y(vis_row)
        ts = _tile_size()
        aj.draw_rectangle(sx, sy, sx + ts, sy + ts, outline=True, color=aj.c_yellow)

    def _draw_valid_move_hints(self) -> None:
        sc, sr = self.game.selected_col, self.game.selected_row
        if sc is None or sr is None:
            return
        hints = self.game.state.legal_moves(sc, sr)
        ts = _tile_size()
        flipped = self.game.my_role == Role.black
        for hint in hints:
            vis_col = GRID_SIZE - 1 - hint.to_col if flipped else hint.to_col
            vis_row = GRID_SIZE - 1 - hint.to_row if flipped else hint.to_row
            cx = _col_x(vis_col) + ts / 2
            cy = _row_y(vis_row) + ts / 2
            target = self.game.state.get(hint.to_col, hint.to_row)
            radius = 4 if target is not None else 3
            alpha = 0.4 if target is not None else 0.5
            aj.draw_circle(cx, cy, radius, color=aj.c_lime, alpha=alpha)

    def _draw_drag(self) -> None:
        if self.game.drag_col is None or self.game.drag_row is None:
            return
        assert sprites is not None
        px = self.game.drag_x - _tile_size() / 2
        py = self.game.drag_y - _tile_size() / 2
        piece = self.game.state.get(self.game.drag_col, self.game.drag_row)
        if piece is not None:
            offset = (_tile_size() - _sprite_size()) // 2
            frame = _frame_index(piece.piece_type, piece.colour)
            aj.draw_sprite(
                px + offset, py + offset, sprites, frame, x_scale=1.1, y_scale=1.1
            )


class TurnDisplay(aj.GameObject):
    game: Game

    def __init__(self, game: Game, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(0, 0, **kwargs)
        self.game = game

    @override
    def draw(self) -> None:
        _ensure_assets()
        assert font is not None
        assert _win_font is not None
        assert _prompt_font is not None
        px = _board_offset_x + _tile_size() * GRID_SIZE + 10
        ay = 10
        aj.draw_set_font(font)
        if self.game.game_over:
            aj.draw_set_font(_win_font)
            aj.draw_rectangle(px, ay, px + 200, ay + 40, color=aj.c_black)
            winner = self.game.winner
            assert winner is not None
            color_name = winner.name_title
            aj.draw_text(px + 10, ay + 4, f"{color_name} wins!", aj.c_white)
            aj.draw_set_font(_prompt_font)
            aj.draw_text(px + 20, ay + 44, "Press R to restart", aj.c_white)
        else:
            status = self.game.lobby_status
            if status == LobbyStatus.WAITING:
                text = "Waiting for opponent..."
                color = aj.c_yellow
            elif status == LobbyStatus.MATCH_FOUND:
                short_id = (
                    self.game.opponent_id[:8] if self.game.opponent_id else "??????"
                )
                text = f"Matched! {short_id} vs you"
                color = aj.c_lime
            elif status == LobbyStatus.OPPONENT_LEFT:
                text = "Opponent disconnected"
                color = aj.c_orange
            else:
                is_your_turn = False
                if (
                    self.game.my_role == Role.white
                    and self.game.current_turn == Role.white
                ):
                    is_your_turn = True
                elif (
                    self.game.my_role == Role.black
                    and self.game.current_turn == Role.black
                ):
                    is_your_turn = True
                turn_text = "Your turn" if is_your_turn else "Opponent's turn"
                text = f"{turn_text}".strip()
                color = aj.c_white
            _ = _draw_wrapped_text(px, ay, text, color, panel_width=PANEL_WIDTH - 20)


def _draw_wrapped_text(
    x: float,
    y: float,
    text: str,
    color: aj.Color,
    *,
    max_width: float = 0.0,
    panel_width: float = 0.0,
    line_height: float = 18.0,
) -> int:
    """Draw text wrapped to max_width. Returns number of lines drawn."""
    assert _prompt_font is not None
    aj.draw_set_font(_prompt_font)
    effective_max = panel_width if panel_width > 0 else max_width
    if effective_max <= 0:
        effective_max = _room_width() - x - 20
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
        aj.draw_text(x + 10, y + i * line_height + 2, line_text, color)
    return len(lines)


@final
class InputHandler(aj.GameObject):
    game: Game
    width: float
    height: float
    client: aj.GameNetClient | None
    my_id: str | None

    def __init__(
        self,
        game: Game,
        client: aj.GameNetClient | None,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(0, 0, **kwargs)
        self.game = game
        self.width = _tile_size() * GRID_SIZE
        self.height = _tile_size() * GRID_SIZE
        self.client = client
        self.my_id = None

    def _is_my_turn(self) -> bool:
        if not self.game.my_role:
            return False
        if self.game.my_role == Role.white:
            return self.game.current_turn == Role.white
        return self.game.current_turn == Role.black

    @override
    def step(self) -> None:
        # Drain packets
        if self.client:
            raw = self.client.recv()
            while raw is not None:
                pkt = decode(raw)
                if pkt is None:
                    raw = self.client.recv()
                    continue

                if isinstance(pkt, AssignId):
                    self.my_id = pkt.sender_id.hex[:8]
                    self.game.message_log.append(
                        (f"Connected as {self.my_id}", aj.c_lime)
                    )
                elif isinstance(pkt, GameStart):
                    is_white = (
                        self.my_id is not None and pkt.white_id.hex[:8] == self.my_id
                    )
                    self.game.my_role = Role.white if is_white else Role.black
                    if is_white and pkt.black_id is not None:
                        self.game.opponent_id = pkt.black_id.hex[:8]
                    elif not is_white:
                        self.game.opponent_id = pkt.white_id.hex[:8]
                    self.game.message_log.append(
                        (f"Match started! You are {self.game.my_role}", aj.c_lime)
                    )
                elif isinstance(pkt, LobbyUpdate):
                    self.game.lobby_status = pkt.status
                    if pkt.white_id and pkt.black_id:
                        self.game.opponent_id = (
                            f"{pkt.white_id.hex[:8]} vs {pkt.black_id.hex[:8]}"
                        )
                    self.game.message_log.append((f"Lobby: {pkt.status}", aj.c_gray))
                elif isinstance(pkt, MoveResult):
                    if pkt.success:
                        self.game.message_log.append(("", aj.c_lime))
                    else:
                        self.game.message_log.append(
                            (f"Rejected: {pkt.error}", aj.c_red)
                        )
                elif isinstance(pkt, GameOver):
                    self.game.winner = Role(pkt.winner)
                    self.game.lobby_status = LobbyStatus.GAME_OVER
                    self.game.message_log.append(
                        (f"Game over: {self.game.winner.name_title} wins!", aj.c_lime)
                    )
                elif isinstance(pkt, BoardStateWire):
                    raw_grid = pkt.grid
                    if len(raw_grid) != 64:
                        self.game.message_log.append(("Board data invalid", aj.c_red))
                        raw = self.client.recv()
                        continue
                    new_grid_rows: list[list[PieceData | None]] = [
                        [None] * GRID_SIZE for _ in range(GRID_SIZE)
                    ]
                    for idx in range(64):
                        val = raw_grid[idx]
                        if val != 0:
                            ptype = PieceType((val >> 4) & 0xF)
                            clr = Role(val & 0xF)
                            r = idx // 8
                            c = idx % 8
                            new_grid_rows[r][c] = PieceData(ptype, clr)
                    self.game.state = BoardState(
                        tuple(tuple(new_grid_rows[r]) for r in range(GRID_SIZE))
                    )
                    self.game.current_turn = Role(pkt.next_turn)
                    self.game.lobby_status = LobbyStatus.PLAYING
                    self.game.selected_col = None
                    self.game.selected_row = None
                    self.game.drag_col = None
                    self.game.drag_row = None
                    self.game.message_log.append(("", aj.c_gray))
                elif isinstance(pkt, ClientDisconnected):
                    short = pkt.client_id.hex[:8]
                    self.game.message_log.append((f"{short} left", aj.c_orange))
                    if (
                        self.game.opponent_id is not None
                        and pkt.client_id.hex[:8] == self.game.opponent_id
                    ):
                        self.game.lobby_status = LobbyStatus.OPPONENT_LEFT
                        self.game.opponent_left = True
                elif isinstance(pkt, ClientConnected):
                    short = pkt.client_id.hex[:8]
                    self.game.message_log.append((f"{short} joined", aj.c_lime))
                self.game.message_log = self.game.message_log[-20:]
                raw = self.client.recv()

        # Game over
        if self.game.game_over and aj.keyboard_check(ord("r")):
            self.game.reset()
            self.game.lobby_status = LobbyStatus.REJOINING
            self.game.message_log.append(("Rejoining...", aj.c_yellow))
            if self.client:
                self.client.send(Join().encode())
            return

        # Mouse interaction (only during your turn, playing)
        if (
            self.game.my_role
            and self.game.lobby_status == LobbyStatus.PLAYING
            and not self.game.opponent_left
            and self._is_my_turn()
            and not self.game.game_over
        ):
            flipped = self.game.my_role == Role.black
            if self.game.drag_col is not None:
                room_x, room_y = _mouse_room_position()
                screen_col = int((room_x - _board_offset_x) // _tile_size())
                screen_row = int((room_y - _board_offset_y) // _tile_size())
                self.game.drag_x = room_x
                self.game.drag_y = room_y
                if not aj.mouse_check_button(aj.mb_left):
                    dc = self.game.drag_col
                    dr = self.game.drag_row
                    logical_col, logical_row = _cell_at(screen_col, screen_row, flipped)
                    if (
                        dr is not None
                        and 0 <= logical_col < GRID_SIZE
                        and 0 <= logical_row < GRID_SIZE
                    ):
                        if self.client:
                            self.client.send(
                                MoveRequest(
                                    from_col=dc,
                                    from_row=dr,
                                    to_col=logical_col,
                                    to_row=logical_row,
                                ).encode()
                            )
                    self.game.clear_selection()
            else:
                room_x, room_y = _mouse_room_position()
                screen_col = int((room_x - _board_offset_x) // _tile_size())
                screen_row = int((room_y - _board_offset_y) // _tile_size())
                logical_col, logical_row = _cell_at(screen_col, screen_row, flipped)
                if 0 <= logical_col < GRID_SIZE and 0 <= logical_row < GRID_SIZE:
                    if aj.mouse_check_button_pressed(aj.mb_left):
                        cell = self.game.state.get(logical_col, logical_row)
                        if cell is not None and cell.colour == self.game.current_turn:
                            self.game.clear_selection()
                            self.game.selected_col = logical_col
                            self.game.selected_row = logical_row
                            self.game.drag_col = logical_col
                            self.game.drag_row = logical_row
                            self.game.drag_x = room_x
                            self.game.drag_y = room_y

    @override
    def draw(self) -> None:
        _ensure_assets()
        assert _prompt_font is not None
        aj.draw_set_font(_prompt_font)
        for i, (line, color) in enumerate(self.game.message_log):
            if line:
                y = _board_offset_y + _tile_size() * GRID_SIZE + 10 + i * 18
                aj.draw_text(
                    _board_offset_x + _tile_size() * GRID_SIZE + 10, y, line, color
                )


# ── Main ──────────────────────────────────────────────────────────────────


async def main() -> None:
    # pygame.init() must be called before any pygame/SDL operations.
    import pygame as _pg

    _ = _pg.init()  # ensure display subsystem
    _ensure_assets()

    rw = _room_width()
    rh = _room_height()

    aj.room_set_caption("Chess Multiplayer")
    aj.room_set_size(rw, rh)
    aj.window_set_size(int(rw * WINDOW_SCALE), int(rh * WINDOW_SCALE))
    aj.room_set_background(aj.c_navy)
    aj.view_set_wport(aj.view_current, rw)
    aj.view_set_hport(aj.view_current, rh)

    game = Game(state=initial_board(), current_turn=Role.white)
    client: aj.GameNetClient | None = None
    try:
        client = aj.GameNetClient("wss://ajishio.tbat.me/chess")
        await client.connect()
        print("Connected to server")
    except Exception as e:
        print(f"Failed to connect to multiplayer server: {e}")
        raise

    aj.register_objects(BoardRenderer, TurnDisplay, InputHandler)
    br = BoardRenderer(game)
    br.persistent = True
    aj.add_object(br)
    td = TurnDisplay(game)
    td.persistent = True
    aj.add_object(td)
    ih = InputHandler(game, client)
    ih.persistent = True
    aj.add_object(ih)

    await aj.game_start_async()


if __name__ == "__main__":
    asyncio.run(main())
