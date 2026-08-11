"""Shared chess domain model — single source of truth for both server and client.

Exported types:
    Colour, PieceType, PieceData, Move, BoardState
    legal_moves_for, apply_move, initial_board
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto

GRID_SIZE: int = 8


# ── Enums ───────────────────────────────────────────────────────────────────


class PieceType(IntEnum):
    king = auto()
    queen = auto()
    bishop = auto()
    knight = auto()
    rook = auto()
    pawn = auto()


class Role(IntEnum):
    white = auto()
    black = auto()

    @property
    def opposite(self) -> Role:
        return Role.black if self == Role.white else Role.white

    @property
    def row_start(self) -> int:
        return GRID_SIZE - 1 if self == Role.white else 0

    @property
    def pawn_start_row(self) -> int:
        return self.row_start - 1 if self == Role.white else self.row_start + 1

    @property
    def name_title(self) -> str:
        return self.name.capitalize()


# ── Domain types ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PieceData:
    piece_type: PieceType
    colour: Role


CellData = PieceData | None
CellGrid = tuple[tuple[CellData, ...], ...]


@dataclass(frozen=True)
class Move:
    from_col: int
    from_row: int
    to_col: int
    to_row: int


# ── Geometry helpers ────────────────────────────────────────────────────────

_DIAGONALS: tuple[tuple[int, int], ...] = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_STRAIGHTS: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
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


def _in_bounds(col: int, row: int) -> bool:
    return 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE


def _slide(
    state: BoardState,
    col: int,
    row: int,
    colour: Role,
    dirs: tuple[tuple[int, int], ...],
    out: list[Move],
) -> None:
    for dc, dr in dirs:
        nc, nr = col + dc, row + dr
        while _in_bounds(nc, nr):
            target = state.get(nc, nr)
            if target is None:
                out.append(Move(col, row, nc, nr))
            elif target.colour != colour:
                if target.piece_type != PieceType.king:
                    out.append(Move(col, row, nc, nr))
                break
            else:
                break
            nc += dc
            nr += dr


def _path_clear(state: BoardState, c1: int, r1: int, c2: int, r2: int) -> bool:
    dc = (1 if c2 > c1 else -1) if c2 != c1 else 0
    dr = (1 if r2 > r1 else -1) if r2 != r1 else 0
    c, r = c1 + dc, r1 + dr
    while (c, r) != (c2, r2):
        if state.get(c, r) is not None:
            return False
        c += dc
        r += dr
    return True


def _find_king(state: BoardState, colour: Role) -> tuple[int, int] | None:
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE):
            cell = state.get(col, row)
            if cell is not None and cell.piece_type == PieceType.king and cell.colour == colour:
                return (col, row)
    return None


def _piece_attacks_square(
    state: BoardState,
    col: int,
    row: int,
    colour: Role,
    target_col: int,
    target_row: int,
) -> bool:
    cell = state.get(col, row)
    if cell is None:
        return False
    ptype = cell.piece_type
    match ptype:
        case PieceType.pawn:
            direction = -1 if colour == Role.white else 1
            return abs(target_col - col) == 1 and target_row == row + direction
        case PieceType.knight:
            return (abs(target_col - col), abs(target_row - row)) in ((1, 2), (2, 1))
        case PieceType.king:
            return max(abs(target_col - col), abs(target_row - row)) == 1
        case PieceType.bishop:
            return abs(target_col - col) == abs(target_row - row) and _path_clear(
                state, col, row, target_col, target_row
            )
        case PieceType.rook:
            return (col == target_col or row == target_row) and _path_clear(
                state, col, row, target_col, target_row
            )
        case PieceType.queen:
            is_diag = abs(target_col - col) == abs(target_row - row)
            is_straight = col == target_col or row == target_row
            return (is_diag or is_straight) and _path_clear(state, col, row, target_col, target_row)
        case _:  # pyright: ignore[reportUnnecessaryComparison]
            raise AssertionError(f"unhandled piece type {ptype}")  # pyright: ignore[reportUnreachable]


def _is_king_in_check(state: BoardState, colour: Role) -> bool:
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


def _pseudo_valid_moves_for(state: BoardState, col: int, row: int) -> list[Move]:
    """Return all geometrically possible moves (ignores check)."""
    cell = state.get(col, row)
    if cell is None:
        return []
    ptype, colour = cell.piece_type, cell.colour
    moves: list[Move] = []

    match ptype:
        case PieceType.pawn:
            direction = -1 if colour == Role.white else 1
            fwd = (col, row + direction)
            if _in_bounds(*fwd) and state.get(*fwd) is None:
                moves.append(Move(col, row, fwd[0], fwd[1]))
                if row == colour.pawn_start_row:
                    fwd2 = (col, row + 2 * direction)
                    if _in_bounds(*fwd2) and state.get(*fwd2) is None:
                        moves.append(Move(col, row, fwd2[0], fwd2[1]))
            for dx in (-1, 1):
                diag = (col + dx, row + direction)
                if _in_bounds(*diag):
                    target = state.get(*diag)
                    if (
                        target is not None
                        and target.colour != colour
                        and target.piece_type != PieceType.king
                    ):
                        moves.append(Move(col, row, diag[0], diag[1]))
        case PieceType.knight:
            for dc, dr in _KNIGHT_L:
                nc, nr = col + dc, row + dr
                if _in_bounds(nc, nr):
                    target = state.get(nc, nr)
                    if target is None or (
                        target.colour != colour and target.piece_type != PieceType.king
                    ):
                        moves.append(Move(col, row, nc, nr))
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
                        if target is None or (
                            target.colour != colour and target.piece_type != PieceType.king
                        ):
                            moves.append(Move(col, row, nc, nr))
    return moves


# ── Public API ──────────────────────────────────────────────────────────────


def is_king_in_check(state: BoardState, colour: Role) -> bool:
    return _is_king_in_check(state, colour)


def is_check(state: BoardState, colour: Role) -> bool:
    """Alias for is_king_in_check."""
    return _is_king_in_check(state, colour)


def is_checkmate(state: BoardState, colour: Role) -> bool:
    """Check if a colour is in checkmate."""
    if not _is_king_in_check(state, colour):
        return False
    for c in range(GRID_SIZE):
        for r in range(GRID_SIZE):
            cell = state.get(c, r)
            if cell is not None and cell.colour == colour:
                if legal_moves_for(state, c, r):
                    return False
    return True


def legal_moves_for(state: BoardState, col: int, row: int) -> list[Move]:
    """Return geometrically valid moves that don't leave the owning king in check."""
    cell = state.get(col, row)
    if cell is None:
        return []
    colour = cell.colour
    pseudo = _pseudo_valid_moves_for(state, col, row)
    return [m for m in pseudo if not _is_king_in_check(apply_move(state, m), colour)]


def apply_move(state: BoardState, move: Move) -> BoardState:
    """Apply a move. Handles pawn promotion to queen automatically."""
    cell = state.get(move.from_col, move.from_row)
    assert cell is not None
    ptype, colour = cell.piece_type, cell.colour
    new_state = state.set(move.from_col, move.from_row, None)
    to_piece = PieceData(ptype, colour)
    if ptype == PieceType.pawn and move.to_row == colour.opposite.row_start:
        to_piece = PieceData(PieceType.queen, colour)
    return new_state.set(move.to_col, move.to_row, to_piece)


def initial_board() -> BoardState:
    """Create the starting board state."""
    rows: list[list[CellData]] = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
    back_row: tuple[PieceType, ...] = (
        PieceType.rook,
        PieceType.knight,
        PieceType.bishop,
        PieceType.queen,
        PieceType.king,
        PieceType.bishop,
        PieceType.knight,
        PieceType.rook,
    )
    for col, ptype in enumerate(back_row):
        rows[Role.white.row_start][col] = PieceData(ptype, Role.white)
        rows[Role.black.row_start][col] = PieceData(ptype, Role.black)
    for col in range(GRID_SIZE):
        rows[Role.white.pawn_start_row][col] = PieceData(PieceType.pawn, Role.white)
        rows[Role.black.pawn_start_row][col] = PieceData(PieceType.pawn, Role.black)
    return BoardState(tuple(tuple(r) for r in rows))


# ── BoardState methods (forward refs to module-level functions) ──────────────


@dataclass(frozen=True)
class BoardState:
    """Immutable board state."""

    grid: CellGrid

    def get(self, col: int, row: int) -> CellData:
        return self.grid[row][col]

    def set(self, col: int, row: int, value: CellData) -> BoardState:
        new_row = tuple(self.grid[row][:col]) + (value,) + tuple(self.grid[row][col + 1 :])
        return BoardState(tuple(self.grid[:row]) + (new_row,) + tuple(self.grid[row + 1 :]))

    def is_legal(self, move: Move) -> bool:
        return (
            0 <= move.from_col < GRID_SIZE
            and 0 <= move.from_row < GRID_SIZE
            and 0 <= move.to_col < GRID_SIZE
            and 0 <= move.to_row < GRID_SIZE
        )

    def apply(self, move: Move) -> BoardState:
        return apply_move(self, move)

    def legal_moves(self, col: int, row: int) -> list[Move]:
        return legal_moves_for(self, col, row)

    def is_check(self, colour: Role) -> bool:
        return is_king_in_check(self, colour)

    def is_checkmate(self, colour: Role) -> bool:
        return is_checkmate(self, colour)

    @property
    def is_finished(self) -> bool:
        return _find_king(self, Role.white) is None or _find_king(self, Role.black) is None

    def check_winner(self) -> Role | None:
        if is_checkmate(self, Role.white):
            return Role.black
        if is_checkmate(self, Role.black):
            return Role.white
        return None

    @staticmethod
    def initial() -> BoardState:
        return initial_board()
