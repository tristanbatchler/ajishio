## 11. The Dual-Field Transport Design

### Why one `self.ws` field does not work

The original code had:

```python
self.ws: "js.WebSocket | None" = None
```

This type annotation was applied to _both_ the browser JS WebSocket object
_and_ the desktop `websockets.ClientConnection`.  This caused a cascade of
type errors because the two types have incompatible interfaces:

| Operation | `js.WebSocket` | `websockets.ClientConnection` |
|---|---|---|
| Sending data | `ws.send(data)` — sync, returns `None` | `await ws.send(data)` — async coroutine |
| Closing | `ws.close()` — sync | `await ws.close()` — async coroutine |
| Receiving | via `onmessage` callback | `async for msg in ws:` |

basedpyright, correctly analysing both code paths simultaneously, saw that
`self.ws.send(data)` returned `None` (from the `js.WebSocket` stub) and
therefore `run_task(self.ws.send(data))` was passing `None` to a function
expecting a coroutine — a genuine error.

### The fix: two fields, each with the right type

```python
# In Transport.__init__:
self._js_ws: "js.WebSocket | None" = None      # browser path only
self._desktop_ws: "ClientConnection | None" = None  # desktop path only
```

Each field is only ever written and read in its own platform's code path.
The type checker sees exactly the right type in each context:

- `self._js_ws.send(data)` → `None` → no `run_task` needed → correct
- `self._desktop_ws.send(data)` → `Coroutine[Any, Any, None]` → needs `run_task` → correct
- `async for msg in self._desktop_ws:` → `ClientConnection` is async-iterable → correct

### The `cast` at assignment

```python
self._js_ws = cast(js.WebSocket, js.eval(f"new WebSocket({json.dumps(self.url)})"))
```

`js.eval()` is typed as returning `JSObject` (i.e., `object`).  `cast` tells
the type checker "trust me, this is a `js.WebSocket`".  This is safe because
the surrounding `if hasattr(js, "WebSocket"):` guard confirms the class exists
and `new WebSocket(url)` always returns a `WebSocket` instance in JS.

### Keeping JS callbacks alive: the GC trap

This was discovered by observing that `on_message` silently never fired in the
real browser, even though DevTools confirmed the WebSocket was receiving frames.

When you write:

```python
def on_message(event): ...
self._js_ws.onmessage = on_message
```

the assignment goes through the Emscripten bridge.  JavaScript does not receive
the Python function itself — it receives a **proxy wrapper** object.  The proxy
holds a weak handle back into the Python heap.  If Python's garbage collector
later reclaims the original callable (because nothing else references it), the
proxy becomes a dangling pointer.  JavaScript still believes the handler is
registered, but calling it either does nothing or crashes silently.

The fix is to keep a strong Python reference on the `Transport` instance for
as long as the socket exists:

```python
# In Transport.__init__:
self._on_open:    "Callable[[js.Event], None] | None"    = None
self._on_message: "Callable[[js.MessageEvent], None] | None" = None
self._on_error:   "Callable[[js.Event], None] | None"    = None
self._on_close:   "Callable[[js.Event], None] | None"    = None
```

Then in `_connect_browser`, after defining the closures, store them **before**
assigning to the JS object:

```python
self._on_open    = on_open
self._on_message = on_message
self._on_error   = on_error
self._on_close   = on_close

self._js_ws.onopen    = self._on_open
self._js_ws.onmessage = self._on_message
self._js_ws.onerror   = self._on_error
self._js_ws.onclose   = self._on_close
```

Now the `Transport` object owns a live reference to every callback.  As long
as `Transport` is alive, the callbacks cannot be garbage collected, and the
JavaScript proxy remains valid.

**Symptom checklist** — if you see this bug in the future:

- WebSocket connects successfully (`onopen` fired, `self.opened` is `True`).
- Messages are visible in the browser's DevTools Network tab.
- Python's `on_message` never runs; `self.inbox` stays empty.
- No exceptions anywhere.

The cause is almost always a missing strong reference to the callback.

---
