import asyncio
import json
import socket
import sys
from asyncio import Task
from collections.abc import Awaitable, Callable, Coroutine
from typing import TYPE_CHECKING, Any, cast

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

        self.inbox: list[bytes] = []
        self.opened: bool = False
        self.open_error: str | None = None
        self.closed: bool = False

        # Strong references to Python callback functions used by the browser
        # WebSocket event system.
        #
        # Why needed:
        # JavaScript stores proxy wrappers around Python callables. If Python no
        # longer references the original function, it may be garbage-collected,
        # causing onmessage/onopen/etc to silently stop firing.
        #
        # Keeping them on self ties callback lifetime to the Transport object.
        self._on_open: Callable[[js.Event], None] | None = None
        self._on_message: Callable[[js.MessageEvent], None] | None = None
        self._on_error: Callable[[js.Event], None] | None = None
        self._on_close: Callable[[js.Event], None] | None = None

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
            import js

            def _arraybuffer_to_bytes(payload: js.ArrayBuffer) -> bytes:
                csv = cast(
                    js.JSFunction,
                    js.eval("(x) => Array.from(new Uint8Array(x)).join(',')"),
                )(payload)
                text = str(csv)
                if not text:
                    return b""
                return bytes(int(part) for part in text.split(","))

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

                def on_open(event: js.Event) -> None:
                    print("NET DEBUG: JS websocket open", event)
                    self.opened = True

                def on_message(event: js.MessageEvent) -> None:
                    print("NET DEBUG: JS websocket message", event)
                    payload = event.data
                    print("NET DEBUG: JS websocket onmessage", payload)

                    if isinstance(payload, str):
                        self.inbox.append(payload.encode("utf-8"))
                    else:
                        self.inbox.append(_arraybuffer_to_bytes(payload))

                def on_error(event: js.Event) -> None:
                    print("NET DEBUG: JS websocket onerror", event)
                    self.open_error = event.type

                def on_close(event: js.Event) -> None:
                    print("NET DEBUG: JS websocket onclose", event)
                    self.closed = True

                # IMPORTANT: retain callback refs
                self._on_open = on_open
                self._on_message = on_message
                self._on_error = on_error
                self._on_close = on_close

                self._js_ws.onopen = self._on_open
                self._js_ws.onmessage = self._on_message
                self._js_ws.onerror = self._on_error
                self._js_ws.onclose = self._on_close

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
        import websockets

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
                    self.inbox.append(msg)
                else:
                    self.inbox.append(msg.encode("utf-8"))
        except Exception as exc:
            print("NET DEBUG: desktop websocket reader exception", exc)

    async def _reader_browser(self) -> None:
        """Pump data from the raw fallback socket into ``inbox``."""
        import select

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
            self.inbox.append(data)

    # ------------------------------------------------------------------
    # Send / recv / close
    # ------------------------------------------------------------------

    def send(self, data: str | bytes) -> None:
        print(
            f"NET DEBUG: send() _IS_BROWSER={_IS_BROWSER} len={len(data)} data={data}"
        )

        if _IS_BROWSER:
            if self._js_ws is not None:
                try:
                    import js

                    if isinstance(data, bytes):
                        csv = ",".join(str(b) for b in data)
                        byte_array = js.eval(f"new Uint8Array([{csv}])")
                        self._js_ws.send(byte_array)
                    else:
                        self._js_ws.send(data)

                    print("NET DEBUG: send() browser JS websocket send complete")
                except Exception as exc:
                    print("NET DEBUG: send() browser JS websocket error", exc)
                return

            if self.sock is None:
                print("NET DEBUG: send() socket not open")
                return

            try:
                raw = data if isinstance(data, bytes) else data.encode("utf-8")
                _ = self.sock.send(raw)
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
        if not self.inbox:
            return None

        return self.inbox.pop(0)

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
# GameNetClient
# ---------------------------------------------------------------------------


class GameNetClient:
    """Thin, protocol-agnostic wrapper around ``Transport``.

    Sends and receives raw strings/bytes only.  All packet encoding and
    decoding is the responsibility of the caller.
    """

    def __init__(self, host: str = "ws://localhost:8765") -> None:
        self.transport: Transport = Transport(host)
        self.connected: bool = False

    async def connect(self) -> None:
        await self.transport.connect()
        self.connected = True

    def send(self, data: str | bytes) -> None:
        """Send a raw string or bytes to the server."""
        self.transport.send(data)

    def recv(self) -> bytes | None:
        """Return the next queued message as raw bytes, or None if inbox is empty."""
        return self.transport.recv()

    async def run(self) -> None:
        """Yield to the event loop each frame. Use as a background task."""
        while not should_exit():
            await sleep0()

    def close(self) -> None:
        self.transport.close()
