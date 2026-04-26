from typing import Any

class WebSocket:
    binaryType: str
    onopen: Any
    onmessage: Any
    onerror: Any
    onclose: Any

    def __init__(self, url: str) -> None: ...
    def send(self, data: str) -> None: ...
    def close(self) -> None: ...

def eval(code: str) -> Any: ...

console: Any
