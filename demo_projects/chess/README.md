# Chess — MVP

Naive piece pickup/putdown on a standard 8×8 board. No chess rules enforced yet — just the board and drag-to-move pieces.

## Run

```
uv run -m demo_projects.chess.main
```

## Controls

- **Left click** a piece to select it, **left click** a tile to move it.
- Clicking an occupied tile **captures** the piece there.
- Click the same piece again to **deselect**.
- **ESC** to restart.

## Files

- `main.py` — game logic
- `sprites/chess_pieces.png` — 270×90 sheet (2 rows × 6 columns of 45×45 pieces)
- `sprites/chess_pieces.json` — frame metadata (12 frames: 6 types × 2 colors; order matches `Board.Pieces` enum)
