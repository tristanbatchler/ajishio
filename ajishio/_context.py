from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ajishio.engine import Engine

# Set once in ajishio/__init__.py before any game logic runs.
# Internal modules import this module (not the value) so the lookup is always fresh.
# cast(None) is a safe sentinel: type checkers see Engine, runtime sees None until __init__.py runs.
engine: Engine = cast("Engine", cast(object, None))
