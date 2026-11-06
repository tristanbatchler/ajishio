"""
What only a web page has: the address it was opened at, and storage that outlives it. Everything
here is safe to call on the desktop, where there's no address and nothing is stored.
"""

from __future__ import annotations

import json
import sys

is_browser: bool = sys.platform == "emscripten"


def _js_eval_string(source: str) -> str:
    import js  # noqa: PLC0415 - only exists in the browser

    return str(js.eval(source))


def browser_query_param(name: str) -> str | None:
    """A parameter from the page's address (`?name=value`), if it has it."""
    if not is_browser:
        return None
    value = _js_eval_string(
        f"new URLSearchParams(location.search).get({json.dumps(name)}) ?? ''"
    )
    return value or None


def browser_storage_get(key: str) -> str | None:
    """Read from the browser's localStorage. Private windows can refuse, which reads as nothing."""
    if not is_browser:
        return None
    try:
        return (
            _js_eval_string(f"localStorage.getItem({json.dumps(key)}) ?? ''") or None
        )
    except Exception:  # noqa: BLE001 - whatever the browser raises, it's just not there
        return None


def browser_storage_set(key: str, value: str) -> bool:
    """Write to the browser's localStorage. Returns whether it worked."""
    if not is_browser:
        return False
    try:
        _ = _js_eval_string(
            f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)}); 'ok'"
        )
    except Exception:  # noqa: BLE001 - private windows and full quotas
        return False
    return True
