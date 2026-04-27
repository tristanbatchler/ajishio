from typing import Callable

JSValue = str | int | float | bool | None | dict[str, "JSValue"] | list["JSValue"]
JSObject = object

class Event:
    type: str
    target: JSObject
    currentTarget: JSObject
    isTrusted: bool

class MessageEvent(Event):
    class BinaryData:
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
    def send(self, data: str | bytes) -> None: ...
    def close(self) -> None: ...


def eval(code: str) -> JSObject: ...

console: JSObject
