# Web Export

Ajishio projects can be exported to run in the browser via
[pygbag](https://github.com/nicegui-org/pygbag). No changes to your game code are required.

## Usage

From the repository root:

```bash
uv run pygbag_export.py demo_projects/sokoban
```

This starts a local test server at [http://localhost:8000](http://localhost:8000). Open it in a
Chromium-based browser (Chrome, Edge, Brave) for best results.

Other useful flags:

```bash
# Build only, don't start the server
uv run pygbag_export.py demo_projects/sokoban --build

# Build a zip you can upload to itch.io
uv run pygbag_export.py demo_projects/sokoban --build --archive
```

Output goes to `<your_project>/_web_build/`.

## What the export script does

The script takes care of everything so you don't have to think about it:

1. Copies your project into a temporary build directory (your source files are never modified)
2. Bundles the ajishio library alongside your project
3. Patches the copied `main.py` for the browser:
    - Adds `import pygame` so pygbag downloads the pygame-ce WebAssembly wheel
    - Adds `import asyncio` if not already present
    - Swaps `aj.game_start()` → `asyncio.run(aj.async_game_start())` so the game loop yields
      to the browser every frame

## Debugging

If you see a blank grey screen, append `?-i` to the URL
(e.g. [http://localhost:8000?-i](http://localhost:8000?-i)). This opens a Python terminal at the
bottom of the page where you can see tracebacks and print output.

## Known limitations

- **`cProfile`** doesn't exist in WebAssembly. Ajishio handles this internally, but avoid
  importing `cProfile` or `pstats` directly in your game code.
- **`from __future__ import annotations`** — add this to your `main.py` if you use type hints
  behind `if TYPE_CHECKING` guards. pygbag evaluates annotations eagerly.
