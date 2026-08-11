from __future__ import annotations
import ajishio as aj
from dataclasses import dataclass
from enum import IntEnum, auto
from pathlib import Path
from typing import Literal, Unpack, override

GRID_SIZE: int = 8
PANEL_WIDTH: int = 260
PieceNotation = Literal["K", "Q", "B", "N", "R", ""]

_DIAGONALS: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)
_STRAIGHTS: tuple[tuple[int, int], ...] = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
)
_KNIGHT_L: tuple[tuple[int, int], ...] = (
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
)


@dataclass(frozen=True)
class Move:
    from_col: int
    from_row: int
    to_col: int
    to_row: int


# ── Assets ────────────────────────────────────────────────────────────────────

_project_dir = Path(__file__).parent
sprites = aj.load_aseprite_sprite(_project_dir / "sprites")
font = aj.load_font(_project_dir / "CutiveMono-Regular.ttf", 20)
_label_font = aj.load_font(_project_dir / "CutiveMono-Regular.ttf", 16)
_win_font = aj.load_font(_project_dir / "CutiveMono-Regular.ttf", 28)
_prompt_font = aj.load_font(_project_dir / "CutiveMono-Regular.ttf", 16)
TILE_SIZE = max(sprites.width, 72)
SPRITE_SIZE = sprites.width
board_size = GRID_SIZE * TILE_SIZE

_board_offset_x: float = 0.0
_board_offset_y: float = 0.0
_COLUMN_LABELS: str = "abcdefgh"
_RANK_LABELS: str = "87654321"
_room_width: int = PANEL_WIDTH + board_size
_room_height: int = board_size


def _col_x(col: int) -> float:
    return _board_offset_x + col * TILE_SIZE


def _row_y(row: int) -> float:
    return _board_offset_y + row * TILE_SIZE


def _frame_index(ptype: PieceType, colour: Colour) -> int:
    return (ptype.value - 1) * 2 + colour.value - 1


# ── Types ─────────────────────────────────────────────────────────────────────


class PieceType(IntEnum):
    king = auto()
    queen = auto()
    bishop = auto()
    knight = auto()
    rook = auto()
    pawn = auto()

    def symbol(self) -> PieceNotation:
        match self:
            case PieceType.king:
                return "K"
            case PieceType.queen:
                return "Q"
            case PieceType.bishop:
                return "B"
            case PieceType.knight:
                return "N"
            case PieceType.rook:
                return "R"
            case PieceType.pawn:
                return ""


class Colour(IntEnum):
    white = auto()
    black = auto()

    @property
    def row_start(self) -> int:
        return GRID_SIZE - 1 if self == Colour.white else 0

    @property
    def pawn_start_row(self) -> int:
        return self.row_start - 1 if self == Colour.white else self.row_start + 1

    @property
    def opposite(self) -> Colour:
        return Colour.black if self == Colour.white else Colour.white

    @property
    def name_title(self) -> str:
        return self.name.capitalize()


@dataclass(frozen=True)
class PieceData:
    piece_type: PieceType
    colour: Colour


CellData = PieceData | None

CellGrid = tuple[tuple[CellData, ...], ...]


# ── Board state ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BoardState:
    grid: CellGrid

    def get(self, col: int, row: int) -> CellData:
        return self.grid[row][col]

    def set(self, col: int, row: int, value: CellData) -> BoardState:
        new_cell_row = (
            tuple(self.grid[row][:col]) + (value,) + tuple(self.grid[row][col + 1 :])
        )
        new_grid = (
            tuple(self.grid[:row]) + (new_cell_row,) + tuple(self.grid[row + 1 :])
        )
        return BoardState(new_grid)

    @staticmethod
    def initial() -> BoardState:
        # Build empty board: rows[row][col]
        rows: list[list[CellData]] = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]

        back_row_order: list[PieceType] = [
            PieceType.rook,
            PieceType.knight,
            PieceType.bishop,
            PieceType.queen,
            PieceType.king,
            PieceType.bishop,
            PieceType.knight,
            PieceType.rook,
        ]

        def _place_back_row(colour: Colour) -> None:
            for col, ptype in enumerate(back_row_order):
                row = colour.row_start
                rows[row][col] = PieceData(ptype, colour)

        def _place_pawns(colour: Colour) -> None:
            for col in range(GRID_SIZE):
                row = colour.pawn_start_row
                rows[row][col] = PieceData(PieceType.pawn, colour)

        _place_back_row(Colour.white)
        _place_pawns(Colour.white)
        _place_back_row(Colour.black)
        _place_pawns(Colour.black)

        return BoardState(tuple(tuple(row) for row in rows))


# ── Game logic ────────────────────────────────────────────────────────────────


def _in_bounds(col: int, row: int) -> bool:
    return 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE


def _pseudo_valid_moves_for(state: BoardState, col: int, row: int) -> list[Move]:
    """Return all geometrically possible moves for the piece at (col, row).

    Does not check whether the move leaves the owning colour's king in check.
    """
    cell = state.get(col, row)
    if cell is None:
        return []
    ptype, colour = cell.piece_type, cell.colour
    moves: list[Move] = []

    match ptype:
        case PieceType.pawn:
            direction = -1 if colour == Colour.white else 1
            forward = (col, row + direction)
            if _in_bounds(*forward) and state.get(*forward) is None:
                moves.append(
                    Move(
                        from_col=col, from_row=row, to_col=forward[0], to_row=forward[1]
                    )
                )
                if row == colour.pawn_start_row:
                    ahead = (col, row + 2 * direction)
                    if _in_bounds(*ahead) and state.get(*ahead) is None:
                        moves.append(
                            Move(
                                from_col=col,
                                from_row=row,
                                to_col=ahead[0],
                                to_row=ahead[1],
                            )
                        )
            for dx in (-1, 1):
                diag = (col + dx, row + direction)
                if _in_bounds(*diag):
                    target = state.get(*diag)
                    if target is not None and target.colour != colour:
                        moves.append(
                            Move(
                                from_col=col,
                                from_row=row,
                                to_col=diag[0],
                                to_row=diag[1],
                            )
                        )
        case PieceType.knight:
            for dc, dr in _KNIGHT_L:
                nc, nr = col + dc, row + dr
                if _in_bounds(nc, nr):
                    target = state.get(nc, nr)
                    if target is None or target.colour != colour:
                        moves.append(
                            Move(from_col=col, from_row=row, to_col=nc, to_row=nr)
                        )
        case PieceType.bishop:
            _slide(state, col, row, colour, _DIAGONALS, moves)
        case PieceType.rook:
            _slide(state, col, row, colour, _STRAIGHTS, moves)
        case PieceType.queen:
            _slide(state, col, row, colour, _DIAGONALS + _STRAIGHTS, moves)
        case PieceType.king:
            for dc in range(-1, 2):
                for dr in range(-1, 2):
                    if dc == 0 and dr == 0:
                        continue
                    nc, nr = col + dc, row + dr
                    if _in_bounds(nc, nr):
                        target = state.get(nc, nr)
                        if target is None or target.colour != colour:
                            moves.append(
                                Move(from_col=col, from_row=row, to_col=nc, to_row=nr)
                            )
    return moves


def _slide(
    state: BoardState,
    col: int,
    row: int,
    colour: Colour,
    dirs: tuple[tuple[int, int], ...],
    out: list[Move],
) -> None:
    for dc, dr in dirs:
        nc, nr = col + dc, row + dr
        while _in_bounds(nc, nr):
            target = state.get(nc, nr)
            if target is None:
                out.append(Move(from_col=col, from_row=row, to_col=nc, to_row=nr))
            elif target.colour != colour:
                out.append(Move(from_col=col, from_row=row, to_col=nc, to_row=nr))
                break
            else:
                break
            nc += dc
            nr += dr


@dataclass
class Game:
    state: BoardState
    current_turn: Colour
    selected_col: int | None = None
    selected_row: int | None = None
    drag_col: int | None = None
    drag_row: int | None = None
    drag_x: float = 0.0
    drag_y: float = 0.0

    @staticmethod
    def new() -> Game:
        return Game(
            state=BoardState.initial(),
            current_turn=Colour.white,
            selected_col=None,
            selected_row=None,
        )

    def clear_selection(self) -> None:
        self.selected_col = None
        self.selected_row = None

        self.drag_col = None
        self.drag_row = None
        self.drag_x = 0.0
        self.drag_y = 0.0

    def try_move(self, move: Move) -> bool:
        if not _in_bounds(move.from_col, move.from_row):
            return False
        if not _in_bounds(move.to_col, move.to_row):
            return False
        from_cell = self.state.get(move.from_col, move.from_row)
        if from_cell is None or from_cell.colour != self.current_turn:
            return False
        pseudo = _legal_moves_for(self.state, move.from_col, move.from_row)
        if move not in pseudo:
            return False
        self.state = _apply_move(self.state, move)
        self.current_turn = from_cell.colour.opposite
        # Check for king capture (should not happen with proper check detection)
        if _find_king(self.state, self.current_turn) is None:
            self._winner = from_cell.colour
        else:
            # Check for checkmate: current player has no legal moves and is in check
            if _is_king_in_check(self.state, self.current_turn):
                all_moves: list[Move] = []
                for c in range(GRID_SIZE):
                    for r in range(GRID_SIZE):
                        cell = self.state.get(c, r)
                        if cell is not None and cell.colour == self.current_turn:
                            all_moves.extend(_legal_moves_for(self.state, c, r))
                if not all_moves:
                    self._winner = from_cell.colour
        self.clear_selection()
        return True

    @property
    def game_over(self) -> bool:
        return self._winner is not None

    @property
    def winner(self) -> Colour | None:
        return self._winner

    _winner: Colour | None = None

    def reset(self) -> None:
        """Reset to a fresh game."""
        self.state = BoardState.initial()
        self.current_turn = Colour.white
        self.selected_col = None
        self.selected_row = None
        self.drag_col = None
        self.drag_row = None
        self._winner = None


def _find_king(state: BoardState, colour: Colour) -> tuple[int, int] | None:
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE):
            cell = state.get(col, row)
            if (
                cell is not None
                and cell.piece_type == PieceType.king
                and cell.colour == colour
            ):
                return (col, row)
    return None


def _is_king_in_check(state: BoardState, colour: Colour) -> bool:
    """Return True if the given colour's king is under attack."""
    king = _find_king(state, colour)
    if king is None:
        return False
    kcol, krow = king
    opponent = colour.opposite
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE):
            cell = state.get(col, row)
            if cell is None or cell.colour != opponent:
                continue
            if _piece_attacks_square(state, col, row, opponent, kcol, krow):
                return True
    return False


def _piece_attacks_square(
    state: BoardState,
    col: int,
    row: int,
    colour: Colour,
    target_col: int,
    target_row: int,
) -> bool:
    """Check if a piece at (col, row) can geometrically strike (target_col, target_row)."""
    cell = state.get(col, row)
    if cell is None:
        return False
    ptype = cell.piece_type
    match ptype:
        case PieceType.pawn:
            direction = -1 if colour == Colour.white else 1
            return abs(target_col - col) == 1 and target_row == row + direction
        case PieceType.knight:
            diff_col = abs(target_col - col)
            diff_row = abs(target_row - row)
            return (diff_col, diff_row) in ((1, 2), (2, 1))
        case PieceType.king:
            return max(abs(target_col - col), abs(target_row - row)) == 1
        case PieceType.bishop:
            return _is_diagonal(col, row, target_col, target_row) and _path_clear(
                state, col, row, target_col, target_row
            )
        case PieceType.rook:
            return _is_straight(col, row, target_col, target_row) and _path_clear(
                state, col, row, target_col, target_row
            )
        case PieceType.queen:
            return (
                _is_diagonal(col, row, target_col, target_row)
                or _is_straight(col, row, target_col, target_row)
            ) and _path_clear(state, col, row, target_col, target_row)


def _is_diagonal(col1: int, row1: int, col2: int, row2: int) -> bool:
    return abs(col2 - col1) == abs(row2 - row1)


def _is_straight(col1: int, row1: int, col2: int, row2: int) -> bool:
    return col1 == col2 or row1 == row2


def _path_clear(state: BoardState, col1: int, row1: int, col2: int, row2: int) -> bool:
    """Return True if the path from (col1,row1) to (col2,row2) is clear (exclusive of endpoints)."""
    dc = (1 if col2 > col1 else -1) if col2 != col1 else 0
    dr = (1 if row2 > row1 else -1) if row2 != row1 else 0
    col, row = col1 + dc, row1 + dr
    while (col, row) != (col2, row2):
        if state.get(col, row) is not None:
            return False
        col += dc
        row += dr
    return True


def _legal_moves_for(state: BoardState, col: int, row: int) -> list[Move]:
    """Return geometrically valid moves that don't leave the owning king in check."""
    cell = state.get(col, row)
    if cell is None:
        return []
    colour = cell.colour
    pseudo = _pseudo_valid_moves_for(state, col, row)
    return [m for m in pseudo if not _is_king_in_check(_apply_move(state, m), colour)]


def _apply_move(state: BoardState, move: Move) -> BoardState:
    """Apply move to state and return new state.

    Handles promotion: pawns reaching the opponent's back row become queens.
    """
    cell = state.get(move.from_col, move.from_row)
    assert cell is not None
    ptype, colour = cell.piece_type, cell.colour
    new_state = state.set(move.from_col, move.from_row, None)
    to_piece = PieceData(ptype, colour)
    if ptype == PieceType.pawn and move.to_row == colour.opposite.row_start:
        to_piece = PieceData(PieceType.queen, colour)
    new_state = new_state.set(move.to_col, move.to_row, to_piece)
    return new_state


# ── Mouse helpers ────────────────────────────────────────────────────────────


def _mouse_room_position() -> tuple[float, float]:
    win_w = aj.window_width
    vp_w = aj.view_wport[aj.view_current]
    vp_x = aj.view_xport[aj.view_current]
    scale = vp_w / win_w if win_w > 0 else 1.0
    return (
        (aj.mouse_x - vp_x) * scale,
        (aj.mouse_y - aj.view_yport[aj.view_current]) * scale,
    )


# ── Game objects ─────────────────────────────────────────────────────────────


class BoardRenderer(aj.GameObject):
    game: Game

    def __init__(self, game: Game, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(0, 0, **kwargs)
        self.game = game

    @override
    def draw(self) -> None:
        self._draw_board_background()
        self._draw_pieces()
        self._draw_selection()
        self._draw_valid_move_hints()
        self._draw_drag()

    def _draw_board_background(self) -> None:
        aj.draw_rectangle(
            _board_offset_x,
            _board_offset_y,
            _board_offset_x + board_size,
            _board_offset_y + board_size,
            color=aj.c_black,
        )
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                x, y = _col_x(col), _row_y(row)
                color = aj.c_ltgray if (col + row) % 2 == 0 else aj.c_dkgray
                aj.draw_rectangle(x, y, x + TILE_SIZE, y + TILE_SIZE, color=color)
        aj.draw_rectangle(
            _board_offset_x,
            _board_offset_y,
            _board_offset_x + board_size,
            _board_offset_y + board_size,
            outline=True,
        )
        self._draw_labels()

    def _draw_labels(self) -> None:
        aj.draw_set_font(_label_font)
        for i in range(GRID_SIZE):
            # Column labels bottom-right of bottom row
            cx = _col_x(i) + TILE_SIZE - 14
            cy = _row_y(GRID_SIZE - 1) + TILE_SIZE - 22
            aj.draw_text(cx, cy, _COLUMN_LABELS[i], aj.c_white)
            # Row labels top-left of left column
            cx = _col_x(0) + 4
            cy = _row_y(i) + 8
            aj.draw_text(cx, cy, _RANK_LABELS[i], aj.c_white)

    def _draw_pieces(self) -> None:
        game = self.game
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                if (
                    game.drag_col is not None
                    and col == game.drag_col
                    and row == game.drag_row
                ):
                    continue
                cell = game.state.get(col, row)
                if cell is None:
                    continue
                px, py = _col_x(col), _row_y(row)
                offset = (TILE_SIZE - SPRITE_SIZE) // 2
                frame = _frame_index(cell.piece_type, cell.colour)
                aj.draw_sprite(px + offset, py + offset, sprites, frame)

    def _draw_selection(self) -> None:
        game = self.game
        sc = game.selected_col
        sr = game.selected_row
        if sc is None or sr is None:
            return
        sx = _col_x(sc)
        sy = _row_y(sr)
        aj.draw_rectangle(
            sx, sy, sx + TILE_SIZE, sy + TILE_SIZE, outline=True, color=aj.c_yellow
        )

    def _draw_valid_move_hints(self) -> None:
        game = self.game
        sc = game.selected_col
        sr = game.selected_row
        if sc is None or sr is None:
            return
        hints = _legal_moves_for(game.state, sc, sr)
        for hint in hints:
            cx = _col_x(hint.to_col) + TILE_SIZE / 2
            cy = _row_y(hint.to_row) + TILE_SIZE / 2
            target = game.state.get(hint.to_col, hint.to_row)
            r = 4 if target is not None else 3
            aj.draw_circle(cx, cy, r, color=aj.c_lime, alpha=0.4 if target else 0.5)

    def _draw_drag(self) -> None:
        game = self.game
        if game.drag_col is not None and game.drag_row is not None:
            px = game.drag_x - TILE_SIZE / 2
            py = game.drag_y - TILE_SIZE / 2
            piece = game.state.get(game.drag_col, game.drag_row)
            if piece is not None:
                offset = (TILE_SIZE - SPRITE_SIZE) // 2
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
        aj.draw_set_font(font)
        px = board_size + 10
        ay = 10
        if self.game.winner is not None:
            aj.draw_set_font(_win_font)
            winner = self.game.winner
            text = f"{winner.name.capitalize()} wins!"
            tw = aj.text_width(text)
            aj.draw_rectangle(px, ay, px + tw + 40, ay + 40, color=aj.c_black)
            aj.draw_text(px + 10, ay + 4, text, aj.c_white)
            aj.draw_set_font(_prompt_font)
            prompt = "Press R to restart"
            pw = aj.text_width(prompt)
            aj.draw_text(px + (tw + 40 - pw) / 2, ay + 44, prompt, aj.c_white)
        else:
            text = f"{self.game.current_turn.name_title} to move"
            tw = aj.text_width(text) * 1.3
            aj.draw_rectangle(px, ay, px + tw + 30, ay + 24, color=aj.c_black)
            aj.draw_text(px + 10, ay + 2, text, aj.c_white)


class InputHandler(aj.GameObject):
    game: Game

    def __init__(self, game: Game, **kwargs: Unpack[aj.GameObjectKwargs]) -> None:
        super().__init__(0, 0, **kwargs)
        self.game = game

    @override
    def step(self) -> None:
        if self.game.winner is not None and aj.keyboard_check(ord("r")):
            self.game.reset()
            return
        room_x, room_y = _mouse_room_position()
        col = int((room_x - _board_offset_x) // TILE_SIZE)
        row = int((room_y - _board_offset_y) // TILE_SIZE)
        game = self.game
        if game.drag_col is not None and game.drag_row is not None:
            game.drag_x = room_x
            game.drag_y = room_y
            if not aj.mouse_check_button(aj.mb_left):
                if _in_bounds(col, row):
                    _ = game.try_move(Move(game.drag_col, game.drag_row, col, row))
                game.clear_selection()
                return
        if _in_bounds(col, row):
            if aj.mouse_check_button_pressed(aj.mb_left):
                cell = game.state.get(col, row)
                if cell is not None and cell.colour == game.current_turn:
                    game.clear_selection()
                    game.selected_col = col
                    game.selected_row = row

                    game.drag_col = col
                    game.drag_row = row
                    game.drag_x = room_x
                    game.drag_y = room_y
                    return


# ── Main ──────────────────────────────────────────────────────────────────────


@aj.profile
def main() -> None:
    window_scale = 2
    aj.room_set_caption("Chess")
    aj.room_set_size(_room_width, _room_height)
    aj.window_set_size(
        int(_room_width * window_scale), int(_room_height * window_scale)
    )
    aj.room_set_background(aj.c_navy)
    aj.view_set_wport(aj.view_current, _room_width)
    aj.view_set_hport(aj.view_current, _room_height)
    game = Game.new()
    aj.register_objects(BoardRenderer, TurnDisplay, InputHandler)
    _ = BoardRenderer(game)
    _ = TurnDisplay(game)
    _ = InputHandler(game)
    aj.game_start()


if __name__ == "__main__":
    main()
