## 7. Networking Strategies

The transport layer in `net.py` supports three distinct networking paths,
selected at runtime based on what is available:

### Path A: JS WebSocket (real browser, preferred)

**When used**: `_IS_BROWSER` is `True` AND `hasattr(js, "WebSocket")` is `True`.

This is the cleanest and most capable path.  It uses the browser's native
WebSocket API directly through the `js` module.

```
Python code
    → js.eval("new WebSocket(url)")     ← creates a real browser WebSocket
    → ws.onopen / ws.onmessage etc.     ← Python callbacks registered as JS handlers
    → ws.send(data)                     ← sync call, JS handles async internally
    → self.inbox (list[str])            ← messages queued by on_message callback
```

**Characteristics**:
- Full duplex, event-driven.
- Messages arrive via callback (`on_message`) and are buffered in `self.inbox`.
- `send()` is synchronous from Python's perspective — the browser handles
  buffering and async delivery internally.
- `Transport.send()` accepts both `str` and `bytes`.  Bytes are passed
  directly to the JS WebSocket (which sends them as a binary frame).
- Binary frames arrive as `ArrayBuffer` proxies.  `to_py()` is called on
  the proxy and may return either `str` or `bytes` depending on the frame
  content and pygbag version.  Both cases are handled in `on_message`.

**Why JS WebSocket instead of Python `websockets`?**  
The `websockets` library requires a proper event loop that can do real async
I/O.  The WASM event loop is frame-ticked, not I/O-driven.  Real network I/O
goes through the browser's JS engine.  The `websockets` library cannot hook
into this.

### Path B: Raw TCP socket via pygbag proxy (browser fallback)

**When used**: `_IS_BROWSER` is `True` AND `js.WebSocket` is not available
(e.g., in the simulator or when JS WebSocket creation fails).

```
Python code
    → socket.socket()                   ← looks like normal Python socket
    → aio_sock_open(sock, host, port)   ← async connect (handles EINPROGRESS)
    → _reader_browser() coroutine       ← background loop calling sock.recv()
    → self.inbox                        ← decoded strings from received bytes
```

**Characteristics**:
- Uses Python's `socket` module, which in WASM is bridged through the
  browser's WebSocket-to-TCP proxy.
- Non-blocking.  The `_reader_browser` coroutine uses `select.select` with
  a zero timeout to poll for data without blocking.
- Port numbers are remapped by +20000 (see §8).
- Raw TCP — no WebSocket framing.  Your server must be a plain TCP server.
- Slower to connect than JS WebSocket because it goes through more layers.

### Path C: Desktop `websockets` library (CPython, non-browser)

**When used**: `_IS_BROWSER` is `False`.

```
Python code
    → await websockets.connect(url)     ← standard async WebSocket connection
    → _reader_desktop() coroutine       ← async for msg in connection:
    → self.inbox                        ← decoded strings
```

**Characteristics**:
- Uses the `websockets>=16.0` library (in workspace deps, always available).
- Full async I/O via the standard asyncio event loop.
- `send()` schedules an `async def send()` coroutine via `run_task()`.
- Messages are `str` (text frames) or `bytes` (binary frames) — bytes are
  decoded to `str` before entering `inbox`.

---
