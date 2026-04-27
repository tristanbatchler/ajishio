## 16. Known Gotchas

### 1. `socket.send()` returns `int`, not `None`

`socket.send(data)` returns the number of bytes actually written.  For small
messages this is always `len(data)`, but you should not assume it.  The return
value must be captured (`_ = self.sock.send(...)`) to avoid
`reportUnusedCallResult` warnings, and in production code you should verify
that all bytes were sent.

### 2. Inbox is not framed

The raw socket path (`_reader_browser`) reads up to 4096 bytes per call.  A
single `recv()` may return a partial JSON message or multiple concatenated
messages if the sender writes them in bursts.  The current code treats each
`recv()` as a complete message — this works for small JSON messages but will
break for large payloads.  A production implementation should buffer data and
split on `\n` (JSONL framing).

### 3. `on_message` fires on the JS event loop thread

In a real browser with Pyodide, the JS event loop and the Python event loop
run in the same Web Worker.  `on_message` is called synchronously when the
browser delivers the WebSocket message.  This means it runs between Python
event loop ticks, not inside a coroutine.  Do not `await` anything inside
`on_message`, `on_open`, `on_error`, or `on_close`.

### 4. `aio.exit` is set by pygbag, not by your code

Do not set `aio.exit = True` yourself unless you intend to stop the entire
pygbag runtime.  Use the `should_exit()` helper as a read-only check only.

### 5. The `aio` stub reflects a snapshot in time

The `aio/__init__.pyi` stub was written by inspecting the pygbag 0.9.x
runtime.  If pygbag's internals change in a future version, the stub may drift.
When something type-checks correctly but fails at runtime, check whether the
stub is outdated.

### 6. `js.eval()` exceptions are opaque

If the JavaScript expression passed to `js.eval()` throws, the error arrives
as a Python `Exception` but with limited information.  Wrap `js.eval()` calls
in `try/except` and log the exception type and message for debugging.

### 7. `cast()` is a lie — use it carefully

`cast(SomeType, value)` tells the type checker that `value` is `SomeType` but
does absolutely nothing at runtime.  If you `cast` incorrectly, the bug will
only appear at runtime, not during type checking.  Only use `cast` when you
have verified the actual runtime type via `hasattr`, `isinstance`, or a logical
guarantee (like `if hasattr(js, "WebSocket"):` before casting to `js.WebSocket`).

### 9. JS callback garbage collection (the silent `on_message` trap)

If you assign Python functions to `js.WebSocket` event properties and then
messages stop arriving silently — even though DevTools shows them — the cause
is almost certainly garbage collection.

When you do `self._js_ws.onmessage = on_message`, JavaScript receives a
**proxy wrapper** around the Python callable, not the callable itself.  If
Python drops its reference to the original function, the GC reclaims it.
JavaScript still holds the proxy, but calling it does nothing.

**Fix**: store strong references to every callback on the `Transport` instance:

```python
self._on_open    = on_open
self._on_message = on_message
self._on_error   = on_error
self._on_close   = on_close

self._js_ws.onopen    = self._on_open
self._js_ws.onmessage = self._on_message
```

As long as `Transport` is alive, the callbacks cannot be collected.  See §11
for the full explanation and type annotations.

### 10. The simulator does not emulate everything

The desktop pygbag simulator runs your code in a desktop Python process with a
simulated browser-like environment.  But it does not run a real browser, so:

- `js.WebSocket` may not be available or may behave differently.
- The port +20000 proxy is handled differently.
- Performance characteristics are completely different.

Always validate in a real browser before shipping.

### 11. `to_py()` does not always return `str`

The `js.MessageEvent.BinaryData.to_py()` method converts a JavaScript
`ArrayBuffer` to a Python value.  The stub declares it as `-> str` for
simplicity, but in practice it can return `bytes` depending on the frame
content and the pygbag/Emscripten version in use.

The `on_message` handler accounts for both:

```python
py_payload = payload.to_py()
if isinstance(py_payload, bytes):
    self.inbox.append(py_payload.decode("utf-8", "replace"))
else:
    self.inbox.append(str(py_payload))
```

If you ever update the stub to `-> str | bytes`, remove the `str()` fallback
and let the type checker guide the narrowing.

---
