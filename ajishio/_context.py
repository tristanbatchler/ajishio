from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ajishio.engine import Engine

# Set once in ajishio/__init__.py before any game logic runs.
# Internal modules import this module (not the value) so the lookup is always fresh.
engine: Engine
