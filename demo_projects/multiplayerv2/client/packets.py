"""Chat protocol — packet definitions and codec.

``net.py`` is intentionally unaware of these types.  All wire-format decisions
live here so they can be changed without touching the transport layer.

Wire format
-----------
Each message is a JSON object.  The ``"t"`` key is the packet type tag.

    {"t": "chat", "text": "<message text>"}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

type JSONValue = (
    str | int | float | bool | None | dict[str, JSONValue] | list[JSONValue]
)
type JSON = dict[str, JSONValue]


@dataclass(frozen=True)
class ChatMessage:
    """A single chat line, sent by one client and broadcast to all."""

    text: str

    def encode(self) -> str:
        """Serialise to a JSON string ready to pass to ``GameClient.send``."""
        return json.dumps({"t": "chat", "text": self.text})

    @classmethod
    def decode(cls, data: bytes) -> ChatMessage | None:
        """Try to parse ``data`` as a ``ChatMessage``.

        Returns ``None`` on any error — malformed JSON, wrong type tag,
        missing fields, wrong field types.  Never raises.
        """
        try:
            raw = json.loads(data.decode("utf-8", "replace"))  # pyright: ignore[reportAny]
            if not isinstance(raw, dict):
                return None
            d = cast(dict[str, object], raw)
            if d.get("t") != "chat":
                return None
            text = d.get("text")
            if not isinstance(text, str):
                return None
            return cls(text=text)
        except Exception:
            return None
