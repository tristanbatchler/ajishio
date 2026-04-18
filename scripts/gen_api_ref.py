#!/usr/bin/env python3
"""Generate api.md from ajishio's __all__ exports, linking to original definitions."""

import inspect
import mkdocs_gen_files

import ajishio

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
        obj = getattr(obj, "__wrapped__")

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


def generate_api_md() -> str:
    lines: list[str] = []
    lines.append("# API Reference")
    lines.append("")
    lines.append(
        "This page documents the public `aj.` namespace. All functions and classes listed here are available directly from `ajishio`."
    )
    lines.append("")

    # Group objects by their source module
    grouped: dict[str, list[tuple[str, object]]] = {}
    for name in sorted(ajishio.__all__):
        obj = getattr(ajishio, name, None)
        if obj is None:
            continue
        module = get_source_module(obj)
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
    other = grouped.get("other", [])
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

    return "\n".join(lines)


with mkdocs_gen_files.open("api.md", "w") as f:
    f.write(generate_api_md())

mkdocs_gen_files.set_edit_path("api.md", "scripts/gen_api_ref.py")
