---
applyTo: '**'
---
Use modern Python 3.14:
  - Prefer type inference, but explicitly annotate anything the LSP can't infer. In practice, this often means omitting type hints for variables, but including them for function parameters and no-None return types and class attributes.
  - Use `match` statements instead of chains of `if` `elif` `else` or `if isinstance` checks when matching against types or constant values.
  - Use the walrus operator (`:=`) where it improves readability by reducing redundancy.
  - Use decorators like `@dataclass`, `@cached_property`, and `@functools.cache` to reduce boilerplate and improve performance.
  - Clearly use `@override` when overriding methods from a superclass.
  - Do not use `typing.Any` under any circumstances.
  - Remember that `typing.List`, `typing.Dict`, `typing.Set`, and `typing.Tuple` are deprecated; use the built-in `list`, `dict`, `set`, and `tuple` generics instead.
  - Prefer `|` for union types instead of `Union[]`.
  - Prefer `| None` for optional types instead of `Optional[]`.
  - No need to add `__init__.py` files to declare packages; modern Python supports implicit namespace packages.
  - Always use the `logging` module for logging instead of `print()`. Configure loggers with appropriate handlers for each distinct area of functionality.

I am using `uv` as my build system and workspace manager. Ensure that each package has a `pyproject.toml` file with the correct dependencies and Python version specified. The root `pyproject.toml` should include all packages in the workspace. 

NEVER use relative imports as they are prone to creating circular dependencies. Always use absolute imports from the project root, which will be run as a module thanks to `uv run -m` and the `__main__.py` file in the application root.

NEVER write substantial application logic in `__init__.py` files. The `ajishio/__init__.py` is a deliberate exception: it is the public API facade responsible for singleton creation, init ordering, and namespace flattening — this is package bootstrapping, not application logic. Any game/application logic should reside in other modules.

To break circular imports between interdependent modules (e.g. engine ↔ game objects), use a thin `_context.py` module as a lazy singleton holder. Internal modules import `_context` at module level and access `_ctx.engine` at method-call time rather than import time, so the attribute is resolved after all modules finish loading. Example:
```python
# ajishio/_context.py
from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from ajishio.engine import Engine
engine: Engine = cast("Engine", cast(object, None))
```
Then in game object modules: `import ajishio._context as _ctx` and access `_ctx.engine` inside methods.

All public engine/view API is exposed on the `ajishio` package itself. Game code should use a single `import ajishio as aj` and access everything via `aj.<name>`. Do not import submodules directly in game code.

Make use of `dataclasses` whenever you need simple data containers. They reduce boilerplate code and improve readability. Also make good use of the `abc` module to define abstract base classes for shared interfaces and common functionality.

Always ensure paths are handled with `pathlib`. If you need to ensure the path is relative to the project root instead of where the script is being run from, use `Path(__file__)` and its parents to compute the project root and use the `/` operator to build paths from there.

Don't use magic strings or numbers instead of enums. To define sets of related constants with meaningful names. This improves code readability and helps catch errors at compile time.

Don't abuse dictionaries for data structures, ESPECIALLY not dictionaries with string keys. This is not JavaScript. Use the appropriate Python data structures which support type hints to avoid issues (e.g. typos, repeated literals scattered throughout the codebase, etc.).

Let the code speak for itself and don't add comments that just restate what the code is doing. Use comments to explain why certain decisions were made, any non-obvious behavior, or to provide context that isn't immediately clear from the code itself.
