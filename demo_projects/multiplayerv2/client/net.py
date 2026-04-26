from typing import Callable, cast
from collections.abc import Coroutine, Awaitable
from asyncio import Task

import json
import sys
import time
import asyncio
import socket


def should_exit() -> bool:
    return False


def sleep0() -> Awaitable[None]:
    return asyncio.sleep(0)


def run_task(coro: Coroutine[None, None, None]) -> Task[None]:
    return asyncio.create_task(coro)


_IS_BROWSER = sys.platform == "emscripten"

if _IS_BROWSER:
    import aio

    def should_exit() -> bool:
        return aio.exit

    def sleep0() -> Awaitable[None]:
        return aio.sleep(0)

    def run_task(coro: Coroutine[None, None, None]) -> Task[None]:
        return aio.create_task(coro)


type JSONValue = str | int | float | bool | None | dict[str, JSONValue] | list[JSONValue]
JSON = dict[str, JSONValue]


async def aio_sock_open(sock: socket.socket, host: str, port: int):
    import aio

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
            if exc.errno in (30, 106):
                return sock
            raise


class Transport:
    def __init__(self, url: str):
        self.url: str = url
        self.ws = None
        self.sock: socket.socket | None = None
        self.inbox: list[str] = []
        self.opened = False
        self.open_error = None
        self.closed = False

    @staticmethod
    def _parse_url(url: str) -> tuple[str, int]:
        if url.startswith("ws://") or url.startswith("wss://"):
            url = url.split("://", 1)[1]
        if url.startswith("://"):
            url = url[3:]
        if ":" not in url:
            raise ValueError("Transport URL must be host:port")
        host, port = url.rsplit(":", 1)
        return host, int(port)

    async def connect(self) -> None:
        print(f"NET DEBUG: connect() _IS_BROWSER={_IS_BROWSER} url={self.url}")
        if _IS_BROWSER:
            try:
                import js

                if hasattr(js, "WebSocket"):
                    print("NET DEBUG: browser JS WebSocket available")
                    self.ws = cast(js.WebSocket, js.eval(f"new WebSocket({json.dumps(self.url)})"))
                    self.ws.binaryType = "arraybuffer"
                    self.opened = False
                    self.open_error = None
                    self.closed = False

                    def on_open(event):
                        print("NET DEBUG: JS websocket open", event)
                        self.opened = True

                    def on_message(event):
                        payload = event.data
                        print("NET DEBUG: JS websocket onmessage", payload)
                        if isinstance(payload, str):
                            self.inbox.append(payload)
                        else:
                            try:
                                self.inbox.append(payload.to_py())
                            except Exception:
                                self.inbox.append(bytes(payload))

                    def on_error(event):
                        print("NET DEBUG: JS websocket onerror", event)
                        self.open_error = event

                    def on_close(event):
                        print("NET DEBUG: JS websocket onclose", event)
                        self.closed = True

                    self.ws.onopen = on_open
                    self.ws.onmessage = on_message
                    self.ws.onerror = on_error
                    self.ws.onclose = on_close

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

            import socket

            self.sock = socket.socket()
            host, port = self._parse_url(self.url)
            if not self.url.startswith("://"):
                port += 20000
            print(f"NET DEBUG: browser socket connect host={host} port={port}")
            await aio_sock_open(self.sock, host, port)
            print("NET DEBUG: browser socket connected")
            run_task(self._reader_browser())
            return

        import websockets

        print("NET DEBUG: desktop websocket connect")
        self.ws = await websockets.connect(self.url)
        print(f"NET DEBUG: desktop websocket connected: {self.ws}")
        run_task(self._reader_desktop())

    async def _reader_desktop(self) -> None:
        try:
            async for msg in self.ws:
                print("NET DEBUG: desktop websocket incoming msg type=", type(msg), "value=", msg)
                self.inbox.append(msg)
        except Exception as exc:
            print("NET DEBUG: desktop websocket reader exception", exc)
            return

    async def _reader_browser(self) -> None:
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
            try:
                self.inbox.append(data.decode("utf-8"))
            except Exception:
                self.inbox.append(data)

    def send(self, data: str) -> None:
        print(f"NET DEBUG: send() _IS_BROWSER={_IS_BROWSER} len={len(data)} data={data}")
        if _IS_BROWSER:
            if self.ws is not None and hasattr(self.ws, "send"):
                try:
                    self.ws.send(data)
                    print("NET DEBUG: send() browser JS websocket send complete")
                except Exception as exc:
                    print("NET DEBUG: send() browser JS websocket error", exc)
                return

            if self.sock is None:
                print("NET DEBUG: send() socket not open")
                return
            try:
                self.sock.send(data.encode("utf-8"))
                print("NET DEBUG: send() browser socket send complete")
            except OSError as exc:
                print("NET DEBUG: send error:", exc)
            return

        if self.ws is None:
            print("NET DEBUG: send() websocket not open")
            return

        run_task(self.ws.send(data))
        print("NET DEBUG: send() websocket send scheduled")

    def flush(self) -> None:
        print("NET DEBUG: flush()")
        return

    def recv(self) -> bytes | None:
        # print(f"NET DEBUG: recv() _IS_BROWSER={_IS_BROWSER} inbox_size={len(self.inbox)}")
        if _IS_BROWSER:
            if self.ws is not None and hasattr(self.ws, "onmessage"):
                if not self.inbox:
                    return None
                msg = self.inbox.pop(0)
                if isinstance(msg, str):
                    return msg.encode("utf-8")
                if isinstance(msg, bytes):
                    return msg
                return None

            import select

            if self.sock is None:
                return None

            try:
                ready, _, _ = select.select([self.sock], [], [], 0)
            except Exception as exc:
                print("select error:", exc)
                return None

            if not ready:
                return None

            try:
                data = self.sock.recv(4096)
            except BlockingIOError:
                return None
            except OSError as exc:
                print("recv error:", exc)
                return b""

            return data

        if not self.inbox:
            return None

        msg = self.inbox.pop(0)
        if isinstance(msg, str):
            return msg.encode("utf-8")
        if isinstance(msg, bytes):
            return bytes(msg)
        return None

    def close(self) -> None:
        if _IS_BROWSER:
            if self.sock is None:
                return
            try:
                self.sock.close()
            except Exception as exc:
                print("close error:", exc)
            return

        if self.ws is None:
            return
        run_task(self.ws.close())


class GameClient:
    def __init__(self, host: str = "ws://localhost:8765", nick: str | None = None):
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
            print("NET DEBUG: poll() not connected")
            return

        data = self.transport.recv()
        print(f"NET DEBUG: poll() received raw={data}")
        if data is None or data == b"":
            return

        self.buffer = data.decode("utf-8", "replace")
        print(f"NET DEBUG: poll() decoded buffer={self.buffer}")
        try:
            msg = json.loads(self.buffer)
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
