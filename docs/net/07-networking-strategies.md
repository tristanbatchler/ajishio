## 7. Networking Strategies

The transport layer in `net.py` supports three distinct networking paths,
selected at runtime based on what is available:

The transport in `ajishio/src/ajishio/net.py` has three runtime paths.

### Path A: Browser JS WebSocket (preferred)

Used when `_IS_BROWSER` is true and `js.WebSocket` exists.

```
connect() → _connect_browser()
    → js.eval("new WebSocket(...)")
    → register onopen/onmessage/onerror/onclose
    → inbox receives bytes
```

Current behavior:
- Messages are buffered as `bytes` in `self.inbox`.
- Text frames are encoded with UTF-8 before enqueue.
- Binary frames are converted from `ArrayBuffer` via JS `Uint8Array` helper,
  then enqueued as `bytes`.
- Callback references are stored on `self` (`_on_open`, `_on_message`, etc.) to
  avoid callback proxy lifetime issues.

### Path B: Browser socket fallback

Used when browser mode is active but JS WebSocket creation is unavailable or
fails.

```
connect() → _connect_browser()
    → socket.socket()
    → aio_sock_open(...)
    → run_task(_reader_browser())
```

Current behavior:
- Uses non-blocking socket polling with `select.select(..., timeout=0)`.
- Received chunks are appended directly as `bytes`.
- `recv()` returns from the shared `inbox`, so fallback and non-fallback
  paths consume data through the same queue.
- For non-simulator URLs, the fallback applies `port += 20000`.

Important caveat:
- `_parse_url` requires `host:port` style endpoints. A URL without explicit
  port (for example `wss://example.com/path`) cannot use this fallback path.

### Path C: Desktop websockets

Used when `_IS_BROWSER` is false.

```
connect() → _connect_desktop()
    → await websockets.connect(url)
    → run_task(_reader_desktop())
```

Current behavior:
- Reader appends either binary payloads or UTF-8 encoded text payloads to
  `self.inbox` as `bytes`.
- `send()` schedules `self._desktop_ws.send(...)` via `run_task`.

---
