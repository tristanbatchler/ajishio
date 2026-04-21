"""Export an ajishio project for the web via pygbag.

Usage:
    uv run pygbag_export.py demo_projects/minesweeper [--build]

This script:
  1. Copies your project folder + the ajishio library into a temporary build dir
  2. Patches main.py for pygbag (injects import pygame, import asyncio,
     swaps aj.game_start() for asyncio.run(aj.async_game_start()))
  3. Runs pygbag on the result

No changes to your source code are required.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
AJISHIO_SRC = REPO_ROOT / "ajishio" / "src" / "ajishio"


def _has_import(tree: ast.Module, module: str) -> bool:
    """Check whether `import <module>` exists as a top-level statement."""
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name == module for alias in node.names):
                return True
    return False


def _import_insert_index(tree: ast.Module) -> int:
    """Return the body index right after any `from __future__` imports."""
    idx = 0
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            idx = i + 1
    return idx


def _is_game_start_call(node: ast.AST) -> bool:
    """Match `aj.game_start()` or `<anything>.game_start()` with no args."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "game_start"
        and not node.args
        and not node.keywords
    )


class _GameStartRewriter(ast.NodeTransformer):
    """Rewrite `aj.game_start()` → `asyncio.run(aj.async_game_start())`."""

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        if _is_game_start_call(node.value):
            assert isinstance(node.value, ast.Call)
            assert isinstance(node.value.func, ast.Attribute)
            # aj.async_game_start()
            inner = ast.Call(
                func=ast.Attribute(
                    value=node.value.func.value,
                    attr="async_game_start",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[],
            )
            # asyncio.run(...)
            outer = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="asyncio", ctx=ast.Load()),
                    attr="run",
                    ctx=ast.Load(),
                ),
                args=[inner],
                keywords=[],
            )
            return ast.copy_location(ast.Expr(value=outer), node)
        return self.generic_visit(node)


def patch_main_py(path: Path) -> None:
    """Patch a copied main.py in-place for pygbag compatibility."""
    source = path.read_text()
    tree = ast.parse(source)

    insert_idx = _import_insert_index(tree)

    # Inject missing imports (insert in reverse order so indices stay valid)
    to_inject: list[str] = []
    if not _has_import(tree, "asyncio"):
        to_inject.append("asyncio")
    if not _has_import(tree, "pygame"):
        to_inject.append("pygame")

    for module in reversed(to_inject):
        node = ast.Import(names=[ast.alias(name=module)])
        tree.body.insert(insert_idx, node)

    # Rewrite aj.game_start() → asyncio.run(aj.async_game_start())
    tree = _GameStartRewriter().visit(tree)

    ast.fix_missing_locations(tree)
    path.write_text(ast.unparse(tree))


def export(project_dir: Path, extra_args: list[str]) -> None:
    if not project_dir.is_dir():
        sys.exit(f"Error: {project_dir} is not a directory")
    if not (project_dir / "main.py").exists():
        sys.exit(f"Error: {project_dir / 'main.py'} not found")

    build_dir = project_dir / "_web_build"

    # Clean previous build
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Copy project files (excluding build dir and __pycache__)
    for item in project_dir.iterdir():
        if item.name in ("build", "_web_build", "__pycache__"):
            continue
        dest = build_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(item, dest)

    # Bundle ajishio library
    shutil.copytree(
        AJISHIO_SRC,
        build_dir / "ajishio",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "py.typed"),
    )

    # Patch main.py for pygbag compatibility
    patch_main_py(build_dir / "main.py")

    print(f"Assembled pygbag project in {build_dir}")
    print(f"Running pygbag...")

    app_name = project_dir.name

    # Always use custom template and auto-start
    tmpl_path = REPO_ROOT / "ajishio.tmpl"
    pygbag_args = [
        sys.executable,
        "-m",
        "pygbag",
        f"--app_name={app_name}",
        f"--template={tmpl_path}",
        "--ume_block=0",
        *extra_args,
        str(build_dir),
    ]
    subprocess.run(pygbag_args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export an ajishio project for pygbag")
    parser.add_argument("project", type=Path, help="Path to the project directory")
    args, extra = parser.parse_known_args()
    export(args.project, extra)


if __name__ == "__main__":
    main()
