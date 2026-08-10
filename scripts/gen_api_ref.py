#!/usr/bin/env python3
"""Generate docs/api.md from ajishio's public facade exports."""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
from pathlib import Path
from types import ModuleType

try:
    import mkdocs_gen_files
except ImportError:  # pragma: no cover - optional during normal Python runs
    mkdocs_gen_files = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_API_PATH = REPO_ROOT / "docs" / "api.md"

GENERATED_BANNER = "<!-- AUTO-GENERATED: do not edit manually. Run `uv run python scripts/gen_api_ref.py`. -->"

# Mapping from module names to section titles
SECTION_MAP = {
    "game_object": "Game Objects",
    "engine": "Engine Control",
    "rendering": "Rendering",
    "input": "Input",
    "utils": "Utilities",
    "types": "Types & Constants",
    "view": "View & Window",
    "sprite_loader": "Asset Loaders",
    "sound_loader": "Asset Loaders",
    "level_loader": "Asset Loaders",
    "game_sound": "Audio",
    "colors": "Colors",
    "keys": "Keyboard Constants",
    "live_props": "Live Properties",
}


def get_source_module(obj: object) -> str | None:
    """Return the module name where obj is defined."""
    module = getattr(obj, "__module__", None)
    if isinstance(module, str):
        return module.split(".")[-1]
    return None


def get_original_definition(obj: object) -> str | None:
    """
    Attempt to find the original function/class that an alias points to.
    Returns a fully qualified name suitable for mkdocstrings (e.g., 'ajishio.engine.Engine.game_start').
    """
    # Unwrap any decorators
    while hasattr(obj, "__wrapped__"):
        obj = getattr(obj, "__wrapped__")  # pyright: ignore[reportAny]

    # If it's a bound method, get the unbound function from the class
    if inspect.ismethod(obj) and hasattr(obj, "__self__"):
        cls = obj.__self__.__class__
        func_name = obj.__name__
        if hasattr(cls, func_name):
            return f"{cls.__module__}.{cls.__name__}.{func_name}"

    # If it's a function defined inside a module (like utils.py functions)
    if inspect.isfunction(obj):
        module = inspect.getmodule(obj)
        if module:
            return f"{module.__name__}.{obj.__name__}"

    # If it's a class
    if inspect.isclass(obj):
        return f"{obj.__module__}.{obj.__name__}"

    # Fallback: use the object's own qualname
    qualname = getattr(obj, "__qualname__", None)
    module = getattr(obj, "__module__", None)
    if isinstance(qualname, str) and isinstance(module, str):
        return f"{module}.{qualname}"

    return None


def _load_ajishio_for_introspection() -> ModuleType:
    """Import ajishio with runtime exports available for accurate API introspection."""
    old_docs_mode = os.environ.pop("AJISHIO_DOCS", None)
    _ = os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    try:
        if "ajishio" in sys.modules:
            module = importlib.reload(sys.modules["ajishio"])
        else:
            module = importlib.import_module("ajishio")
    finally:
        if old_docs_mode is not None:
            os.environ["AJISHIO_DOCS"] = old_docs_mode

    return module


def generate_api_md() -> str:
    ajishio = _load_ajishio_for_introspection()

    lines: list[str] = []
    lines.append(GENERATED_BANNER)
    lines.append("")
    lines.append("# API Reference")
    lines.append("")
    lines.append(
        "This page documents the public `aj.` namespace. All functions and classes listed here are available directly from `ajishio`."
    )
    lines.append("")

    # Group objects by their source module
    grouped: dict[str, list[tuple[str, object]]] = {}
    for name in sorted(ajishio.__all__):  # pyright: ignore[reportAny]
        obj = getattr(ajishio, name, None)  # pyright: ignore[reportAny]
        if obj is None:
            continue
        module = get_source_module(obj)  # pyright: ignore[reportAny]
        if module is None:
            module = "other"
        grouped.setdefault(module, []).append((name, obj))

    order = [
        "game_object",
        "engine",
        "rendering",
        "input",
        "utils",
        "types",
        "view",
        "sprite_loader",
        "sound_loader",
        "level_loader",
        "game_sound",
    ]

    for mod in order:
        if mod not in grouped:
            continue
        title = SECTION_MAP.get(mod, mod.replace("_", " ").title())
        lines.append(f"## {title}")
        lines.append("")
        for name, obj in grouped[mod]:
            # Try to get the original definition path
            original = get_original_definition(obj)
            if original:
                lines.append(f"::: {original}")
                lines.append(f"    # Alias: `aj.{name}`")
            else:
                # Fallback to the alias (will likely show as module-attribute)
                lines.append(f"::: ajishio.{name}")
        lines.append("")

    # Handle any uncategorized
    uncategorized: list[tuple[str, object]] = []
    for mod, values in grouped.items():
        if mod not in order:
            uncategorized.extend(values)

    other = uncategorized
    if other:
        lines.append("## Other")
        lines.append("")
        for name, obj in other:
            original = get_original_definition(obj)
            if original:
                lines.append(f"::: {original}")
                lines.append(f"    # Alias: `aj.{name}`")
            else:
                lines.append(f"::: ajishio.{name}")
        lines.append("")

    return "\n".join(lines)


def _write_via_mkdocs(text: str) -> None:
    assert mkdocs_gen_files is not None
    with mkdocs_gen_files.open("api.md", "w") as f:  # pyright: ignore[reportAny]
        f.write(text)  # pyright: ignore[reportAny]
    mkdocs_gen_files.set_edit_path("api.md", "scripts/gen_api_ref.py")  # pyright: ignore[reportAny]


def _is_mkdocs_run() -> bool:
    return mkdocs_gen_files is not None and "MKDOCS_CONFIG_FILE" in os.environ


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate docs/api.md from ajishio exports"
    )
    _ = parser.add_argument(
        "--check", action="store_true", help="Fail if docs/api.md is out of date"
    )
    _ = parser.add_argument(
        "--stdout", action="store_true", help="Print generated markdown"
    )
    args = parser.parse_args()

    text = generate_api_md()

    if _is_mkdocs_run():
        _write_via_mkdocs(text)
        return

    if args.stdout:  # pyright: ignore[reportAny]
        print(text)
        return

    if args.check:  # pyright: ignore[reportAny]
        existing = DOCS_API_PATH.read_text() if DOCS_API_PATH.exists() else ""
        if existing != text:
            raise SystemExit(
                "docs/api.md is out of date. Run `uv run python scripts/gen_api_ref.py`."
            )
        return

    _ = DOCS_API_PATH.write_text(text)


if __name__ == "__main__":
    main()
