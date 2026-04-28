from __future__ import annotations

from typing import Callable, Protocol

JSValue = str | int | float | bool | None | dict[str, JSValue] | list[JSValue]
JSObject = object

class JSFunction(Protocol):
    def __call__(self, *args: JSObject) -> JSObject: ...

class Event:
    type: str
    target: JSObject
    currentTarget: JSObject
    isTrusted: bool

class ArrayBuffer:
    """Opaque JS ArrayBuffer proxy.

    In pygbag, this does not reliably expose a callable `.to_py()`.
    Convert it from real code with JS, e.g.:
    `Array.from(new Uint8Array(buffer))`.
    """

class Uint8Array:
    """Opaque JS Uint8Array proxy.

    Do not assume `.to_py()` exists or is callable in pygbag.
    Prefer constructing/reading via `js.eval(...)` helpers.
    """

class MessageEvent(Event):
    data: str | ArrayBuffer
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
    def send(self, data: str | JSObject) -> None: ...
    def close(self) -> None: ...

def eval(code: str) -> JSObject | JSFunction: ...

console: JSObject
