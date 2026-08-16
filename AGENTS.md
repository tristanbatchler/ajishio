# AGENTS.md

This file is the primary guide for AI coding agents working in this repository.

## Purpose

Ajishio is a pygame-ce based 2D engine with a GameMaker-like API.
Your default goal is to make pragmatic, typed, demo-friendly changes quickly while preserving existing style and behavior.

## Quick Orientation (Read In This Order)

1. Project overview and run basics:
   [README.md](README.md)
2. Docs landing page:
   [docs/index.md](docs/index.md)
3. Public API map:
   [docs/api.md](docs/api.md)
4. Best full gameplay example:
   [demo_projects/platformer/main.py](demo_projects/platformer/main.py)
5. Best networking example:
   [demo_projects/multiplayerv2/client/main.py](demo_projects/multiplayerv2/client/main.py)
   and protocol definitions in
   [demo_projects/multiplayerv2/shared/packets.py](demo_projects/multiplayerv2/shared/packets.py)
6. Engine facade and runtime wiring:
   [ajishio/src/ajishio/__init__.py](ajishio/src/ajishio/__init__.py)
   [ajishio/src/ajishio/engine.py](ajishio/src/ajishio/engine.py)
   [ajishio/src/ajishio/game_object.py](ajishio/src/ajishio/game_object.py)

## Workspace and Commands

- Install and sync environment:
  - `uv sync`
- Run a demo module:
  - `uv run -m demo_projects.platformer.main`
- Type check/lint (configured in workspace):
  - `uv run ruff check .` and `uv run basedpyright .`
- Quick syntax check for a file:
  - `uv run -m py_compile <path>`
- Run docs locally without pygame window init:
  - `AJISHIO_DOCS=1 uv run mkdocs serve`
- Build static docs:
  - `AJISHIO_DOCS=1 uv run mkdocs build --clean`
- Regenerate API reference page:
  - `uv run python scripts/gen_api_ref.py`
- Check API reference is up to date (CI parity):
  - `uv run python scripts/gen_api_ref.py --check`
- Export a demo to web via pygbag wrapper:
  - `uv run pygbag_export.py demo_projects/<demo_name>`

Relevant config:
- Workspace pyproject: [pyproject.toml](pyproject.toml)
- Engine package pyproject: [ajishio/pyproject.toml](ajishio/pyproject.toml)
- Demo package pyproject: [demo_projects/pyproject.toml](demo_projects/pyproject.toml)
- Web export script: [pygbag_export.py](pygbag_export.py)

## First 15 Minutes (New Agent)

1. Confirm the workspace is healthy.
- Run `uv sync` at repo root.
- Run one known demo: `uv run -m demo_projects.hello_world.main`.

2. Build a quick mental model.
- Read [ajishio/src/ajishio/__init__.py](ajishio/src/ajishio/__init__.py) to understand public API exposure.
- Read [ajishio/src/ajishio/engine.py](ajishio/src/ajishio/engine.py) for frame loop/object lifecycle.
- Read [ajishio/src/ajishio/game_object.py](ajishio/src/ajishio/game_object.py) for gameplay hooks and collision helpers.

3. Validate your edit workflow.
- Syntax-check any touched Python file with `uv -m py_compile <path>`.
- Run the linter and type checker on any touched Python file with the commands explained above.
- If behavior changed, run the smallest relevant demo module.

## Task Routing (Where To Look First)

- "How do I call this API?":
  [docs/api.md](docs/api.md)
- "How should a demo be structured?":
  [demo_projects/platformer/main.py](demo_projects/platformer/main.py)
- "How should multiplayer code be structured?":
  [demo_projects/multiplayerv2/client/main.py](demo_projects/multiplayerv2/client/main.py)
  and [demo_projects/multiplayerv2/shared/packets.py](demo_projects/multiplayerv2/shared/packets.py)
- "How do I load LDtk levels?":
  [docs/rooms.md](docs/rooms.md) and [ajishio/src/ajishio/level_loader.py](ajishio/src/ajishio/level_loader.py)
- "How do I load sprites/sounds?":
  [docs/sprites.md](docs/sprites.md), [ajishio/src/ajishio/sprite_loader.py](ajishio/src/ajishio/sprite_loader.py), [ajishio/src/ajishio/sound_loader.py](ajishio/src/ajishio/sound_loader.py)
- "Why does web export behave differently?":
  [docs/web-export.md](docs/web-export.md), [pygbag_export.py](pygbag_export.py), [ajishio/src/ajishio/net.py](ajishio/src/ajishio/net.py)

## Code Style and Architectural Rules

Follow these rules unless the user explicitly asks otherwise.

1. Use modern Python 3.14 style.
- Prefer built-in generics (`list`, `dict`, `set`, `tuple`).
- Prefer `collections.abc` for abstract types (`Iterable`, `Mapping`, etc.).
- Prefer `|` and `| None` unions.
- Prefer `match` where it improves clarity over long conditional chains.
- Avoid `typing.Any`.

2. Keep imports and package usage consistent.
- In game/demo code, use one import style: `import ajishio as aj`.
- Do not use relative imports.
- Use absolute imports from project root modules.

3. Respect engine lifecycle patterns.
- Subclass `aj.GameObject`.
- Override `step` and `draw` with `@override`.
- Call `super().step()` and `super().draw()` when sprite animation/default behavior should be preserved.

4. Keep initialization and context patterns intact.
- `ajishio/src/ajishio/__init__.py` is a deliberate facade/singleton bootstrap.
- Internal engine modules use lazy context via [ajishio/src/ajishio/_context.py](ajishio/src/ajishio/_context.py).
- Do not move gameplay logic into package `__init__.py` files.

5. Prefer typed structures over ad-hoc dictionaries.
- Use dataclasses and typed dicts already established in
  [ajishio/src/ajishio/types.py](ajishio/src/ajishio/types.py).
- Avoid introducing magic strings/numbers when enum-like constants are appropriate.

6. Use pathlib for file paths.
- Resolve project-relative assets with `Path(__file__).parent` patterns.
- Follow examples in demo projects and loaders.

7. Logging and diagnostics.
- Use `logging` for engine/tooling internals.
- Avoid noisy prints in core engine paths unless debugging is explicitly requested.

8. Preserve public API behavior.
- The `ajishio` top-level namespace is the public facade.
- Prefer adding/changing behavior behind existing facade patterns rather than bypassing them.
- Keep mutable live-state expectations intact (`aj.room_width`, `aj.delta_time`, view dicts, etc.).

## How To Find The Best Existing Pattern Fast

For each task, check docs first, then copy a proven demo pattern.

### Sprites and animation
- Docs: [docs/sprites.md](docs/sprites.md)
- Loader code: [ajishio/src/ajishio/sprite_loader.py](ajishio/src/ajishio/sprite_loader.py)
- Example: [demo_projects/platformer/main.py](demo_projects/platformer/main.py)

### Collision and movement
- Core behavior: [ajishio/src/ajishio/game_object.py](ajishio/src/ajishio/game_object.py)
- Spatial queries: [ajishio/src/ajishio/engine.py](ajishio/src/ajishio/engine.py)
- Example physics loop: [demo_projects/platformer/main.py](demo_projects/platformer/main.py)

### Rooms and level loading (LDtk)
- Docs: [docs/rooms.md](docs/rooms.md)
- Loader: [ajishio/src/ajishio/level_loader.py](ajishio/src/ajishio/level_loader.py)
- Example with entities/tiles registration: [demo_projects/platformer/main.py](demo_projects/platformer/main.py)

### Rendering and drawing APIs
- API index: [docs/api.md](docs/api.md)
- Renderer internals: [ajishio/src/ajishio/rendering.py](ajishio/src/ajishio/rendering.py)
- Viewport behavior: [ajishio/src/ajishio/view.py](ajishio/src/ajishio/view.py)
- Advanced draw example: [demo_projects/spinning_cube/main.py](demo_projects/spinning_cube/main.py)

### Audio
- Loader: [ajishio/src/ajishio/sound_loader.py](ajishio/src/ajishio/sound_loader.py)
- Sound wrapper: [ajishio/src/ajishio/game_sound.py](ajishio/src/ajishio/game_sound.py)
- Example usage: [demo_projects/platformer/main.py](demo_projects/platformer/main.py)

### Networking and web runtime behavior
- Networking docs hub: [docs/net/index.md](docs/net/index.md)
- Transport implementation: [ajishio/src/ajishio/net.py](ajishio/src/ajishio/net.py)
- Protocol example: [demo_projects/multiplayerv2/shared/packets.py](demo_projects/multiplayerv2/shared/packets.py)
- Client example: [demo_projects/multiplayerv2/client/main.py](demo_projects/multiplayerv2/client/main.py)

### Tooling and debugging
- VS Code setup/debugging: [docs/vs-code.md](docs/vs-code.md)
- Profiling flow: [docs/profiling.md](docs/profiling.md)
- Docs build process: [docs/contributing.md](docs/contributing.md)

### Web export
- Guide: [docs/web-export.md](docs/web-export.md)
- Export implementation: [pygbag_export.py](pygbag_export.py)

## New Demo Project Checklist

When creating a new demo under `demo_projects/`:

1. Create folder with at least:
- `main.py`
- `README.md`
- optional `sprites/`, `sounds/`, `room_data/`

2. Build around engine idioms:
- `import ajishio as aj`
- one or more `aj.GameObject` subclasses
- `main()` that sets room/window/caption and starts the game

3. If using rooms/entities:
- export LDtk in super simple format
- load with `aj.load_ldtk_levels(...)`
- register all object classes with names matching LDtk entity/layer names

4. If using sprites:
- export Aseprite as png + json in each sprite folder
- load through `aj.load_aseprite_sprites(...)`

5. Keep code typed and editor-friendly:
- use `@override` and `Unpack[aj.GameObjectKwargs]` where appropriate
- preserve existing style in nearby files

6. Verify quickly:
- run module with `uv run -m demo_projects.<name>.main`
- syntax check touched files with `py_compile`
- if web-targeted, test `uv run pygbag_export.py demo_projects/<name>`

7. Document the demo:
- add usage/controls in that demo's README
- add/update docs index pages when requested

## Practical Agent Behavior

- Prefer smallest viable changes.
- Reuse existing engine and demo patterns before inventing new abstractions.
- When uncertain, check the docs page for that topic, then inspect a demo that already does it.
- Validate with a runnable command whenever possible.
- If a change touches runtime or API behavior, mention potential regressions and suggest a quick test.

## Common Gotchas

- Do not import engine internals directly in demo/game code.
  Use `import ajishio as aj` and `aj.<name>`.
- Do not put gameplay/application logic in package `__init__.py` files.
  The engine facade in [ajishio/src/ajishio/__init__.py](ajishio/src/ajishio/__init__.py) is intentional.
- If overriding `step` or `draw`, skipping `super()` can silently break sprite animation behavior.
- LDtk loading expects super simple export structure and matching class names for entities/layers.
- Web export patches `aj.game_start()` to async at build time; avoid assumptions that only desktop runtime exists.
- Keep paths relative to file locations with pathlib (`Path(__file__).parent` patterns).

## Definition Of Done (Agent Checklist)

1. Change is minimal and follows local patterns.
2. Touched files pass quick syntax validation.
3. Relevant demo or command path was run when behavior changed.
4. New demo content includes a concise README when requested.
5. Notes about risk/regression are included for engine-level changes.

## High-Value References

- Engine facade: [ajishio/src/ajishio/__init__.py](ajishio/src/ajishio/__init__.py)
- Main loop and object lifecycle: [ajishio/src/ajishio/engine.py](ajishio/src/ajishio/engine.py)
- Base object behavior: [ajishio/src/ajishio/game_object.py](ajishio/src/ajishio/game_object.py)
- Rendering entry points: [ajishio/src/ajishio/rendering.py](ajishio/src/ajishio/rendering.py)
- API docs source: [docs/api.md](docs/api.md)
- Demo list: [docs/demo-projects.md](docs/demo-projects.md)
- Platformer reference demo: [demo_projects/platformer/main.py](demo_projects/platformer/main.py)
- Multiplayer reference demo: [demo_projects/multiplayerv2/client/main.py](demo_projects/multiplayerv2/client/main.py)
