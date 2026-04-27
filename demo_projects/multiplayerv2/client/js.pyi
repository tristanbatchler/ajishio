from __future__ import annotations

from typing import Callable

type JSValue = str | int | float | bool | None | dict[str, JSValue] | list[JSValue]

# Opaque JS object proxy – used where the exact shape is unknown or irrelevant.
JSObject = object

class Object:
    prototype: JSObject

    @staticmethod
    def keys(obj: JSObject) -> list[str]: ...

class JSON:
    @staticmethod
    def stringify(value: JSValue) -> str: ...

class Event:
    type: str
    target: JSObject
    currentTarget: JSObject
    isTrusted: bool

class MessageEvent(Event):
    """Mirrors the browser ``MessageEvent`` interface.

    ``data`` is either a plain ``str`` (text frame) or a ``BinaryData``
    proxy wrapping a JavaScript ``ArrayBuffer`` (binary frame).  Call
    ``.to_py()`` on the proxy to obtain the decoded string.
    """

    class BinaryData:
        """Pyodide proxy around a JS ``ArrayBuffer`` received over a binary WebSocket frame."""

        def to_py(self) -> str: ...

    data: BinaryData | str
    origin: str
    lastEventId: str
    ports: list[JSObject] | JSObject | None
    source: JSObject | None

class CloseEvent(Event):
    code: int
    reason: str
    wasClean: bool

class ErrorEvent(Event):
    message: str
    error: JSObject | None

EventHandler = Callable[[Event], None]
MessageHandler = Callable[[MessageEvent], None]

class WebSocket:
    binaryType: str
    onopen: EventHandler | None
    onmessage: MessageHandler | None
    onerror: EventHandler | None
    onclose: EventHandler | None

    def __init__(self, url: str) -> None: ...
    def send(self, data: str) -> None: ...
    def close(self) -> None: ...

def eval(code: str) -> JSObject: ...

console: JSObject
