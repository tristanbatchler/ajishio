import asyncio
import json
import socket
import sys
import time
from asyncio import Task
from collections.abc import Awaitable, Coroutine
from typing import TYPE_CHECKING, Any, Callable, cast

if TYPE_CHECKING:
    import js
    from websockets.asyncio.client import ClientConnection


# ---------------------------------------------------------------------------
# Platform abstractions
#
# These three helpers are defined first with asyncio defaults, then
# overridden inside the ``if _IS_BROWSER:`` block so that the browser
# runtime (pygbag's ``aio`` shim) is used instead.  Both definitions share
# the same signature, so callers are always type-safe.
# ---------------------------------------------------------------------------


def should_exit() -> bool:
    return False


def sleep0() -> Awaitable[None]:
    return asyncio.sleep(0)


def run_task(coro: Coroutine[Any, Any, None]) -> Task[None]:  # pyright: ignore[reportExplicitAny]
    return asyncio.create_task(coro)


_IS_BROWSER = sys.platform == "emscripten"

if _IS_BROWSER:
    import aio

    def should_exit() -> bool:
        return aio.exit

    def sleep0() -> Awaitable[None]:
        return aio.sleep(0)

    def run_task(coro: Coroutine[Any, Any, None]) -> Task[None]:  # pyright: ignore[reportExplicitAny]
        return aio.create_task(coro)


# ---------------------------------------------------------------------------
# JSON type aliases
# ---------------------------------------------------------------------------

type JSONValue = str | int | float | bool | None | dict[str, JSONValue] | list[JSONValue]
type JSON = dict[str, JSONValue]


# ---------------------------------------------------------------------------
# Browser socket helper
# ---------------------------------------------------------------------------


async def aio_sock_open(sock: socket.socket, host: str, port: int) -> socket.socket:
    """Async-connect a non-blocking socket (emscripten / pygbag only).

    In the simulator the host/port are embedded in the URL path, so we
    extract them before connecting.
    """
    import aio  # noqa: PLC0415 – browser-only, intentionally deferred

    if getattr(aio.cross, "simulator", False):
        if "/" in host:
            host, trail = host.strip(":/").split("/", 1)
            port = int(trail.rsplit(":", 1)[-1])

    while True:
        try:
            sock.connect((host, port))
            return sock
        except BlockingIOError:
            await aio.sleep(0)
        except OSError as exc:
            # errno 30 = EROFS (emsdk "connected"), 106 = EISCONN (Linux)
            if exc.errno in (30, 106):
                return sock
            raise


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


class Transport:
    """Platform-agnostic WebSocket transport layer.

    Connection strategy
    -------------------
    * **Browser** (emscripten): tries the JS ``WebSocket`` API first.
      Falls back to a raw TCP socket tunnelled through pygbag's proxy when
      ``js.WebSocket`` is not present (e.g., inside the simulator).
    * **Desktop** (CPython): uses the ``websockets`` library directly.

    All received text is decoded to ``str`` and placed into ``inbox``.
    ``recv()`` pops the oldest queued message and returns it as ``bytes``.
    """

    def __init__(self, url: str) -> None:
        self.url: str = url

        # Browser path ─ JS WebSocket proxy object (set when JS WS is available)
        self._js_ws: "js.WebSocket | None" = None
        # Desktop path ─ websockets library connection
        self._desktop_ws: "ClientConnection | None" = None
        # Browser fallback ─ raw TCP socket via pygbag proxy
        self.sock: socket.socket | None = None

        self.inbox: list[str] = []
        self.opened: bool = False
        self.open_error: str | None = None
        self.closed: bool = False

    @staticmethod
    def _parse_url(url: str) -> tuple[str, int]:
        if url.startswith("ws://") or url.startswith("wss://"):
            url = url.split("://", 1)[1]
        if url.startswith("://"):
            url = url[3:]
        if ":" not in url:
            raise ValueError("Transport URL must specify a port: <host>:<port>")
        host, port_str = url.rsplit(":", 1)
        return host, int(port_str)

    # ------------------------------------------------------------------
    # Public connect entry-point
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        print(f"NET DEBUG: connect() _IS_BROWSER={_IS_BROWSER} url={self.url}")
        if _IS_BROWSER:
            await self._connect_browser()
        else:
            await self._connect_desktop()

    # ------------------------------------------------------------------
    # Platform-specific connect implementations
    # ------------------------------------------------------------------

    async def _connect_browser(self) -> None:
        # Prefer the native JS WebSocket API (available in real browser contexts).
        try:
            import js  # noqa: PLC0415

            if hasattr(js, "WebSocket"):
                print("NET DEBUG: browser JS WebSocket available")
                self._js_ws = cast(
                    js.WebSocket,
                    js.eval(f"new WebSocket({json.dumps(self.url)})"),
                )
                self._js_ws.binaryType = "arraybuffer"
                self.opened = False
                self.open_error = None
                self.closed = False

                def on_open(event: "js.Event") -> None:
                    print("NET DEBUG: JS websocket open", event)
                    self.opened = True

                def on_message(event: "js.MessageEvent") -> None:
                    payload = event.data
                    print("NET DEBUG: JS websocket onmessage", payload)
                    if isinstance(payload, str):
                        self.inbox.append(payload)
                    else:
                        # Binary ArrayBuffer proxy → decode via .to_py()
                        self.inbox.append(payload.to_py())

                def on_error(event: "js.Event") -> None:
                    print("NET DEBUG: JS websocket onerror", event)
                    self.open_error = event.type

                def on_close(event: "js.Event") -> None:
                    print("NET DEBUG: JS websocket onclose", event)
                    self.closed = True

                self._js_ws.onopen = on_open
                self._js_ws.onmessage = on_message
                self._js_ws.onerror = on_error
                self._js_ws.onclose = on_close

                for _ in range(200):
                    if self.opened or self.open_error:
                        break
                    await sleep0()

                if self.open_error:
                    raise RuntimeError(f"JS websocket open failed: {self.open_error}")
                if not self.opened:
                    raise RuntimeError("JS websocket open timeout")

                print("NET DEBUG: browser JS WebSocket connected")
                return

        except Exception as exc:
            print("NET DEBUG: JS WebSocket unavailable or failed", exc)

        # Fallback: raw TCP socket via pygbag's WebSocket-to-TCP proxy bridge.
        self.sock = socket.socket()
        host, port = self._parse_url(self.url)
        if not self.url.startswith("://"):
            # pygbag proxy maps ws port N → TCP port N+20000
            port += 20000
        print(f"NET DEBUG: browser socket connect host={host} port={port}")
        _ = await aio_sock_open(self.sock, host, port)
        print("NET DEBUG: browser socket connected")
        _ = run_task(self._reader_browser())

    async def _connect_desktop(self) -> None:
        import websockets  # noqa: PLC0415

        print("NET DEBUG: desktop websocket connect")
        self._desktop_ws = await websockets.connect(self.url)
        print(f"NET DEBUG: desktop websocket connected: {self._desktop_ws}")
        _ = run_task(self._reader_desktop())

    # ------------------------------------------------------------------
    # Background reader coroutines (one per connection path)
    # ------------------------------------------------------------------

    async def _reader_desktop(self) -> None:
        """Pump incoming messages from the ``websockets`` connection into ``inbox``."""
        if self._desktop_ws is None:
            return
        try:
            async for msg in self._desktop_ws:
                print("NET DEBUG: desktop ws msg type=", type(msg), "value=", msg)
                # websockets yields str for text frames, bytes for binary frames.
                if isinstance(msg, bytes):
                    self.inbox.append(msg.decode("utf-8", "replace"))
                else:
                    self.inbox.append(msg)
        except Exception as exc:
            print("NET DEBUG: desktop websocket reader exception", exc)

    async def _reader_browser(self) -> None:
        """Pump data from the raw fallback socket into ``inbox``."""
        import select  # noqa: PLC0415

        while True:
            if self.sock is None:
                return
            try:
                ready, _, _ = select.select([self.sock], [], [], 0)
            except Exception as exc:
                print("NET DEBUG: browser select exception", exc)
                await sleep0()
                continue

            if not ready:
                await sleep0()
                continue

            try:
                data = self.sock.recv(4096)
            except BlockingIOError:
                await sleep0()
                continue
            except OSError as exc:
                print("NET DEBUG: browser recv error", exc)
                return

            if not data:
                print("NET DEBUG: browser socket closed by peer")
                return

            print("NET DEBUG: browser socket recv", data)
            self.inbox.append(data.decode("utf-8", "replace"))

    # ------------------------------------------------------------------
    # Send / recv / close
    # ------------------------------------------------------------------

    def send(self, data: str) -> None:
        print(f"NET DEBUG: send() _IS_BROWSER={_IS_BROWSER} len={len(data)} data={data}")
        if _IS_BROWSER:
            if self._js_ws is not None:
                try:
                    self._js_ws.send(data)
                    print("NET DEBUG: send() browser JS websocket send complete")
                except Exception as exc:
                    print("NET DEBUG: send() browser JS websocket error", exc)
                return

            if self.sock is None:
                print("NET DEBUG: send() socket not open")
                return
            try:
                _ = self.sock.send(data.encode("utf-8"))
                print("NET DEBUG: send() browser socket send complete")
            except OSError as exc:
                print("NET DEBUG: send error:", exc)
            return

        if self._desktop_ws is None:
            print("NET DEBUG: send() websocket not open")
            return
        _ = run_task(self._desktop_ws.send(data))
        print("NET DEBUG: send() websocket send scheduled")

    def flush(self) -> None:
        print("NET DEBUG: flush()")

    def recv(self) -> bytes | None:
        if _IS_BROWSER:
            if self._js_ws is not None:
                # JS WebSocket path: messages arrive via on_message into inbox.
                if not self.inbox:
                    return None
                return self.inbox.pop(0).encode("utf-8")

            # Raw socket fallback: read directly (non-blocking, no background task).
            if self.sock is None:
                return None
            import select  # noqa: PLC0415

            try:
                ready, _, _ = select.select([self.sock], [], [], 0)
            except Exception as exc:
                print("select error:", exc)
                return None

            if not ready:
                return None

            try:
                return self.sock.recv(4096)
            except BlockingIOError:
                return None
            except OSError as exc:
                print("recv error:", exc)
                return b""

        # Desktop path: messages arrive via _reader_desktop into inbox.
        if not self.inbox:
            return None
        return self.inbox.pop(0).encode("utf-8")

    def close(self) -> None:
        if _IS_BROWSER:
            if self._js_ws is not None:
                self._js_ws.close()
            elif self.sock is not None:
                try:
                    self.sock.close()
                except Exception as exc:
                    print("close error:", exc)
            return

        if self._desktop_ws is None:
            return
        _ = run_task(self._desktop_ws.close())


# ---------------------------------------------------------------------------
# GameClient
# ---------------------------------------------------------------------------


class GameClient:
    def __init__(self, host: str = "ws://localhost:8765", nick: str | None = None) -> None:
        self.transport: Transport = Transport(host)
        self.buffer: str = ""
        self.handlers: dict[str, list[Callable[[JSON], None]]] = {}
        self.connected: bool = False
        self.nick: str = nick or f"u_{int(time.time() * 1000) % 100000}"
        self.room: str | None = None

    async def connect(self) -> None:
        await self.transport.connect()
        self.connected = True
        self.send({"t": "hello", "nick": self.nick})

    def on(self, t: str, fn: Callable[[JSON], None]) -> None:
        self.handlers.setdefault(t, []).append(fn)

    def _emit(self, msg: JSON) -> None:
        t = msg.get("t")
        if not isinstance(t, str):
            return
        for handler in self.handlers.get(t, []):
            try:
                handler(msg)
            except Exception as exc:
                print("handler error:", exc)

    def poll(self) -> None:
        if not self.connected:
            return

        data = self.transport.recv()
        if data is None or data == b"":
            return

        self.buffer = data.decode("utf-8", "replace")
        print(f"NET DEBUG: poll() decoded buffer={self.buffer}")
        try:
            msg: JSON = cast(JSON, json.loads(self.buffer))
        except json.JSONDecodeError as exc:
            print("NET DEBUG: poll() json decode failed", exc)
            return

        print(f"NET DEBUG: poll() dispatch msg={msg}")
        self._emit(msg)

    def send(self, obj: JSON) -> None:
        self.transport.send(json.dumps(obj))

    def send_join(self, room: str) -> None:
        self.room = room
        self.send({"t": "join", "room": room})

    def send_state(self, data: JSON) -> None:
        self.send({"t": "state", "room": self.room, "data": data})

    def send_sync(self, data: JSON) -> None:
        self.send({"t": "sync", "room": self.room, "data": data})

    def send_ping(self) -> None:
        self.send({"t": "ping"})

    def recv(self) -> bytes | None:
        return self.transport.recv()

    async def run(self) -> None:
        while not should_exit():
            self.poll()
            await sleep0()

    def close(self) -> None:
        self.transport.close()
