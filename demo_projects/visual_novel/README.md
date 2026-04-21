# Visual Novel

A lightweight VN-style demo that uses a small custom UI layer on top of Ajishio's core engine.

## Highlights
- Dialogue box with typewriter reveal and advance prompt.
- Choice menu with prompt + selector
- Fallback fonts for missing UTF-8 glyphs

## Controls
- Space / Enter: advance dialogue or confirm a choice
- Up / Down: move selection in choice menus

## Run it
From the repo root:

```bash
uv run demo_projects/visual_novel/main.py
```

## Notes
- Fonts live in `demo_projects/visual_novel/fonts/`. Noto Sans is the primary; Symbols/ Symbols2 are
  fallbacks for arrows and other glyphs.
- The UI layer (dialogue, choices, script runner) is scoped to this demo and does not modify the core
  engine. 