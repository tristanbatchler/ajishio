# Multiplayer Networking Internals

A ground-up technical reference for the pygbag browser-networking stack used
in this demo.  Written for a developer who has never seen pygbag's source code
and needs to understand every design decision without having to repeat the
runtime inspection that produced this knowledge.

---

## Table of Contents

1. [What pygbag Actually Does](#1-what-pygbag-actually-does)
2. [The Browser Runtime Environment](#2-the-browser-runtime-environment)
3. [The `aio` Module](#3-the-aio-module)
4. [The `js` Module](#4-the-js-module)
5. [The `aio.cross` Module](#5-the-aiocross-module)
6. [The Simulator vs Real Browser](#6-the-simulator-vs-real-browser)
7. [Networking Strategies](#7-networking-strategies)
8. [The +20000 Port Mapping](#8-the-20000-port-mapping)
9. [Type Checking Across Platforms](#9-type-checking-across-platforms)
10. [The Stub Files](#10-the-stub-files)
11. [The Dual-Field Transport Design](#11-the-dual-field-transport-design)
12. [Platform Abstraction Helpers](#12-platform-abstraction-helpers)
13. [The `GameClient` API](#13-the-gameclient-api)
14. [The `asyncio` Hijack](#14-the-asyncio-hijack)
15. [Data Flow Reference](#15-data-flow-reference)
16. [Known Gotchas](#16-known-gotchas)
17. [Extending This Into the Engine](#17-extending-this-into-the-engine)

---

## 1. What pygbag Actually Does

pygbag is a command-line tool that takes a Python/pygame project and compiles
it to run in a browser via WebAssembly (WASM).  Understanding what it does at
each stage is the key to understanding every networking decision in this demo.

### Build phase

When you run `pygbag .` inside the client directory, it:

1. Packages all Python files and assets into a WASM-loadable archive.
2. Wraps CPython compiled to WASM (via Emscripten) in an HTML/JS shell.
3. Serves the result over a local HTTP dev server (default port 8000).

### Runtime phase

Once the browser loads the page:

1. The Emscripten-compiled CPython boots inside a Web Worker.
2. Before your `main.py` runs, pygbag injects a set of "support modules"
   directly into `sys.modules` — these are not files on disk that you can
   `import` normally; they are constructed entirely in memory and registered
   by pygbag's bootstrap code.
3. Your code then runs inside a cooperative async event loop that is ticked
   by `window.requestAnimationFrame()` — meaning the event loop advances once
   per display frame (~60 times per second), not continuously.

The critical injected modules are `aio`, `aio.cross`, and `js`.  There is no
PyPI package for any of them.  They do not exist on desktop.  This is the
entire source of the cross-platform complexity.

---

## 2. The Browser Runtime Environment

### `sys.platform`

Inside the WASM runtime, `sys.platform == "emscripten"`.  This is the single
most reliable way to detect you are running in the browser:

```python
_IS_BROWSER = sys.platform == "emscripten"
```

basedpyright does NOT narrow through this intermediate variable, so it always
analyses both branches.  This is intentional and important — it means the type
checker sees all code paths, which is what forces us to write fully typed,
platform-agnostic code.

### The event loop

The WASM asyncio loop is not driven by `asyncio.run()` in the normal sense.
Instead, pygbag replaces `asyncio` with its own `aio` module (see §3) and
drives the loop from a JavaScript `requestAnimationFrame` callback.

**Consequence**: you must `await` frequently.  Any synchronous code that runs
for more than ~16 ms will freeze the browser tab.  Every hot loop must contain
an `await sleep0()` (or equivalent) to yield control back to the browser.

### Sockets

WASM Python has a socket module, but the browser sandbox means raw TCP
connections are not possible.  Instead, pygbag provides a WebSocket-to-TCP
proxy bridge.  From Python, you use `socket.socket()` as normal; under the
hood, each connect/send/recv is tunnelled through a WebSocket connection managed
by JavaScript.  This is transparent to Python code but has consequences for
port numbers (see §8).

---

## 3. The `aio` Module

### What it is

`aio` is pygbag's custom async runtime shim.  Its source lives inside the
pygbag package at:

```
pygbag/support/cross/aio/__init__.py
```

It is injected at startup via:

```python
builtins.aio = sys.modules[__name__]  # inside aio/__init__.py
```

This means `aio` is available as a builtin — you can `import aio` from
anywhere inside the WASM runtime without it being a "real" installed package.

### What it contains

`aio` starts by doing `from asyncio import *`, which means it re-exports the
entire standard asyncio API.  It then overrides or augments specific pieces:

| Name | Type | Description |
|---|---|---|
| `aio.exit` | `bool` | Set to `True` by pygbag when the app should close.  Poll this in your main loop to know when to stop. |
| `aio.started` | `bool` | `True` once the event loop has been started. |
| `aio.paused` | `bool` | `True` when the loop is suspended (e.g., loading screen). |
| `aio.sleep(delay)` | `Awaitable[None]` | Identical to `asyncio.sleep`.  Yields control for at least `delay` seconds.  `aio.sleep(0)` yields for one frame. |
| `aio.create_task(coro)` | `Task[T]` | Identical to `asyncio.create_task`.  Schedules a coroutine on the running loop. |
| `aio.run(coro)` | `None` | Like `asyncio.run`, but plugs into the frame-based scheduler instead of blocking. |
| `aio.loop` | `AbstractEventLoop` | The single shared event loop for the WASM runtime. |
| `aio.cross` | module | Platform-detection submodule (see §5). |

### The `from asyncio import *` trick

Because `aio` re-exports all of `asyncio`, code that did `import asyncio` and
then uses `asyncio.sleep`, `asyncio.create_task` etc. will _mostly_ work even
in the browser — because at module-level, `sys.modules["asyncio"] = aio`.
That line is the last thing `aio/__init__.py` does:

```python
sys.modules["asyncio"] = __import__(__name__)
```

So after `aio` loads, `import asyncio` gives you `aio`.  This is why the same
`asyncio.sleep(0)` call works on both desktop and browser — on browser it's
actually `aio.sleep(0)` in disguise.

### Why we don't just use `asyncio` everywhere

The important divergences are:

- `aio.exit` — no equivalent in real asyncio.
- `aio.create_task` stores created tasks in an internal list so pygbag can
  cancel them on shutdown.  Real `asyncio.create_task` does not.
- `aio.sleep(0)` advances the _frame-based_ loop; `asyncio.sleep(0)` on
  desktop advances the _I/O-based_ loop.  The effect is the same for our
  purposes, but the implementation path is different.

Using the `aio.*` names directly (instead of relying on the `sys.modules`
hijack) is more explicit and makes the browser-specific intent clear.

---

## 4. The `js` Module

### What it is

`js` is a proxy to the browser's global JavaScript namespace.  Its source of
truth on Emscripten is a single line inside
`pygbag/support/cross/__EMSCRIPTEN__.py`:

```python
sys.modules["js"] = window.globalThis
```

`window.globalThis` is an Emscripten embed bridge object that reflects the
browser's `window` global.  Every property of `window` becomes an attribute of
the `js` module.  Every method of `window` becomes callable from Python.

### What this means in practice

```python
import js

# Read a browser global
origin = js.location.origin          # → "http://localhost:8000"

# Call a browser API
js.console.log("hello from Python")

# Evaluate arbitrary JavaScript
result = js.eval("1 + 1")            # → 2 (as a Python int proxy)

# Create a JS object
ws = js.eval(f"new WebSocket({url!r})")
```

`js.eval(code: str)` is the escape hatch for anything that the Emscripten
bridge does not expose as a direct attribute.  It evaluates `code` in the
browser's JS engine and returns the result as a Python proxy object.

### The `js.WebSocket` class

Because `js` mirrors `window`, and `window.WebSocket` is the browser's native
WebSocket class, `js.WebSocket` is the browser's WebSocket constructor.
However, creating a WebSocket via `js.WebSocket(url)` directly from Python
does not always work reliably across all pygbag versions.  The safe pattern
used in this codebase is:

```python
self._js_ws = cast(js.WebSocket, js.eval(f"new WebSocket({json.dumps(url)})"))
```

Using `json.dumps(url)` ensures the URL string is correctly quoted for
JavaScript, including handling special characters.

### JS objects from Python's perspective

A value returned from `js.eval()` is not a Python object — it is a _proxy_
that forwards attribute access and method calls to the underlying JavaScript
object.  The important things to know:

- **Attribute access** works normally: `ws.readyState`, `ws.binaryType`
- **Method calls** work normally: `ws.send("hello")`, `ws.close()`
- **Event handler assignment** works by Python assignment:
  `ws.onmessage = my_python_function` — pygbag wraps the Python callable in a
  JS function automatically.
- **Binary data** (e.g., an `ArrayBuffer` received over a binary WebSocket
  frame) arrives as a special proxy object, not as Python `bytes`.  You must
  call `.to_py()` on it to get a Python string.  This is why `on_message` in
  the transport contains the `isinstance(payload, str)` check.

### The `js` module on desktop

`js` does not exist on desktop.  It is only available inside the WASM runtime.
Attempting to `import js` on desktop raises `ModuleNotFoundError`.  This is
why every real import of `js` is either:

- Inside an `if _IS_BROWSER:` block, or
- Inside a `try: import js` block, or
- Under `if TYPE_CHECKING:` only (for type annotations — never executed).

---

## 5. The `aio.cross` Module

### What it is

`aio.cross` is a submodule of `aio` that holds platform-detection state.  Its
source is at `pygbag/support/cross/aio/cross.py`.

### Key attributes

| Name | Type | Default | Meaning |
|---|---|---|---|
| `aio.cross.simulator` | `bool \| None` | `None` | `True` when running in the pygbag desktop simulator (see §6).  `None` or `False` when running in a real browser or on desktop. |
| `aio.cross.scheduler` | `callable \| None` | `None` | The function pygbag uses to reschedule the event loop step.  Internal use only. |

### Why we care about `simulator`

The simulator and the real browser handle WebSocket/socket connections
differently — particularly the URL format.  In the simulator, the server
address is embedded in the URL _path_ in a special format, rather than being a
plain `host:port` pair.  The `aio_sock_open` function in `net.py` checks this:

```python
if getattr(aio.cross, "simulator", False):
    if "/" in host:
        host, trail = host.strip(":/").split("/", 1)
        port = int(trail.rsplit(":", 1)[-1])
```

We use `getattr(..., "simulator", False)` as a defensive call because `aio` is
only available in the browser, and `aio.cross.simulator` could theoretically be
`None` rather than `False` in some contexts.

---

## 6. The Simulator vs Real Browser

pygbag has two runtime modes:

### Real browser (Emscripten, `sys.platform == "emscripten"`)

- CPython compiled to WASM runs inside a browser tab.
- `js` module is the real `window.globalThis`.
- `js.WebSocket` is the real browser WebSocket API.
- Network connections go through the browser's network stack.
- `aio.cross.simulator` is `None` / falsy.

### Desktop simulator (`pygbag.aio`, non-emscripten)

- pygbag provides a Python-side simulation of the WASM environment that runs
  on your normal desktop Python.
- Useful for iteration without having to compile to WASM.
- `aio` is still injected (via `pygbag/aio.py` which imports the support
  module and runs a desktop event loop).
- `js` is injected differently — the desktop simulator uses a stub.
- Socket connections use a different URL encoding format.
- `aio.cross.simulator` is `True`.

### What this means for you

When testing networking locally, you may find yourself in the simulator.
The port +20000 mapping still applies (see §8), but the URL format may differ.
Always test in a real browser before assuming simulator behaviour matches
production.

---

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
- Binary frames arrive as `ArrayBuffer` proxies and must be decoded via
  `.to_py()`.

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

## 8. The +20000 Port Mapping

This is one of the most surprising facts about pygbag networking and is
documented almost nowhere.

### The problem

Browsers cannot make raw TCP connections — only WebSocket connections.
When Python code calls `socket.connect(("localhost", 8765))`, the WASM runtime
cannot literally open a TCP socket.  Instead, it sends a WebSocket connection
request to the pygbag development server.

### The solution

The pygbag dev server (`pygbag .`) includes a WebSocket-to-TCP proxy.  It
listens for WebSocket connections on port `N+20000` and forwards them as raw
TCP to port `N`.

So: if your server listens on TCP port **8765**, the browser socket must
connect to WebSocket port **28765** (= 8765 + 20000).

`net.py` applies this mapping automatically:

```python
if not self.url.startswith("://"):
    port += 20000
```

The `"://"` prefix is a special format used by the simulator where the URL
already encodes the proxy address; in that case no remapping is needed.

### What this means for your server

Your server must listen on a **plain TCP port** — it speaks raw bytes, not
WebSocket framing.  When you connect from the browser via the raw socket path,
the bytes go:

```
Browser Python socket.send(data)
    → WASM bridge (JS WebSocket frame to port N+20000)
    → pygbag dev proxy (unwraps WS, forwards as TCP)
    → your server's TCP socket on port N
```

And in reverse for recv.

### The JS WebSocket path bypasses this

When using `js.WebSocket` (Path A), you connect directly to a `ws://` URL.
The browser's WebSocket speaks to a server that understands WebSocket framing.
If your server only speaks raw TCP, you need a WebSocket wrapper or you use
Path B.  This demo's server is a plain asyncio TCP server, so Path B
(raw socket + proxy) is the correct approach when needed.

---

## 9. Type Checking Across Platforms

### The challenge

The type checker (basedpyright) analyses all code paths simultaneously.  It
does not narrow based on `sys.platform == "emscripten"` when that check is
stored in an intermediate variable like `_IS_BROWSER`.  This means it sees
code that uses `js.WebSocket` AND code that uses
`websockets.ClientConnection` as potentially running in the same context.

### `TYPE_CHECKING` guard

The solution is the standard Python pattern:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import js                                          # never runs at runtime
    from websockets.asyncio.client import ClientConnection  # never runs at runtime
```

`TYPE_CHECKING` is always `False` at runtime and always `True` for the type
checker.  Code inside these blocks exists only for the benefit of the type
checker and never executes.  This allows us to write annotations that reference
`js.WebSocket` and `ClientConnection` without causing `ImportError` on
platforms where those modules don't exist.

### String annotations for inner-function forward references

Python 3.14 implements PEP 649 (lazy evaluation of annotations).  Function
parameter annotations are not evaluated when the function is defined — they are
only evaluated if something accesses `__annotations__`.  This means you can
safely write:

```python
def on_message(event: "js.MessageEvent") -> None:
    ...
```

inside a browser-only code block, even though `js` is not imported at runtime
on desktop.  The string `"js.MessageEvent"` is stored as a string, never
evaluated.  basedpyright resolves it using the `TYPE_CHECKING` import.

The quoted form is preferred over the bare form for browser-only types defined
in nested functions, because it makes the forward-reference intent explicit.

### `Coroutine[Any, Any, None]`

Real Python coroutines (from `async def f() -> None: ...`) have the type
`Coroutine[Any, Any, None]`.  The `Any` values represent the internal yield
and send types, which are implementation details of the coroutine machinery.
This is the correct and accurate type annotation for "a coroutine that returns
None", even though `reportExplicitAny` flags it.  The suppression comment:

```python
def run_task(coro: Coroutine[Any, Any, None]) -> Task[None]:  # pyright: ignore[reportExplicitAny]
```

is intentional and correct — not a hack.

### `cast()` for JS proxy objects

`js.eval(code)` returns `JSObject` (which is just `object` in the stubs —
the exact runtime type is unknowable statically).  When we know the returned
object is a `WebSocket`, we use `cast` to tell the type checker:

```python
self._js_ws = cast(js.WebSocket, js.eval(f"new WebSocket({json.dumps(url)})"))
```

`cast` has no runtime effect — it returns its second argument unchanged.  This
is safe because we are inside `if hasattr(js, "WebSocket"):` which guarantees
`js.WebSocket` exists, and `new WebSocket(url)` in JS is guaranteed to return
a `WebSocket` instance.

---

## 10. The Stub Files

Because `aio` and `js` are injected at runtime and have no installable Python
package, basedpyright cannot find them through normal module resolution.  We
provide hand-written stub files that teach the type checker about their
interfaces.

### How basedpyright finds them

basedpyright adds the directory of the file being analysed to its module search
path.  Since `net.py` lives in `client/`, the type checker looks in `client/`
for modules.  This is how:

- `client/js.pyi` is found when code does `import js`
- `client/aio/__init__.pyi` is found when code does `import aio`
- `client/aio/cross.pyi` is found when code does `import aio.cross` or
  accesses `aio.cross`

No `pyrightconfig.json` or `extraPaths` configuration is needed — the
co-location with `net.py` is enough.

### `client/js.pyi`

Documents the subset of the browser `window` global that this codebase uses:

- `js.WebSocket` — the browser WebSocket class.  Note that `onopen`,
  `onmessage`, `onerror`, `onclose` are typed as nullable callable handlers.
  Setting them to Python functions is how you register event listeners.
- `js.Event` — the base event type passed to `onopen`, `onerror`, `onclose`.
  The `type: str` attribute gives the event type name.
- `js.MessageEvent` — the event passed to `onmessage`.  The `data` attribute
  is either a plain `str` (text frames) or a `BinaryData` proxy (binary frames,
  i.e., ArrayBuffer).
- `js.MessageEvent.BinaryData` — the Pyodide proxy around a JS `ArrayBuffer`.
  Its only useful method from Python is `.to_py() -> str`, which decodes the
  buffer.
- `js.eval(code: str) -> JSObject` — the JS escape hatch.
- `JSObject = object` — used as a stand-in for the opaque proxy type.

### `client/aio/__init__.pyi`

Documents the parts of `aio` that differ from standard asyncio:

- `aio.exit: bool` — the shutdown flag.  Poll in your main loop.
- `aio.sleep(delay: float) -> Awaitable[None]` — identical to `asyncio.sleep`.
- `aio.create_task(coro, ...) -> Task[T]` — identical to `asyncio.create_task`.
- `aio.cross` — re-exported from the `cross` submodule.

The `from . import cross as cross` line uses a _relative_ import so that
basedpyright resolves `aio.cross` to `client/aio/cross.pyi`, not to a
hypothetical top-level `cross` module.

### `client/aio/cross.pyi`

Minimal stub for the platform-detection submodule:

```python
simulator: bool
```

In practice `simulator` can be `None` (unset) or `True`.  We declare it as
`bool` and access it defensively via `getattr(..., "simulator", False)` in
code, which short-circuits the type issue at the call site.

### Maintaining the stubs

When you discover new `js.*` or `aio.*` APIs you want to use, add them to the
appropriate stub file.  The golden rule: only add what you can verify by
inspecting the real runtime object.  Guessing leads to stubs that compile
cleanly but produce runtime errors.

---

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

---

## 12. Platform Abstraction Helpers

Three module-level functions provide a platform-agnostic interface to the three
behaviours that differ between desktop and browser:

```python
def should_exit() -> bool: ...   # check if the app should quit
def sleep0() -> Awaitable[None]: ...  # yield for one event loop tick
def run_task(coro) -> Task[None]: ... # schedule a background coroutine
```

These are defined twice: first with `asyncio` defaults (desktop), then
overridden inside `if _IS_BROWSER:` with `aio`-based implementations:

```python
def should_exit() -> bool:
    return False                          # desktop: never exits via this flag

def should_exit() -> bool:               # browser override
    return aio.exit                       # browser: pygbag sets this on shutdown
```

basedpyright sees both definitions as having the same signature, so callers
are always type-safe regardless of which definition is active at runtime.

**Important**: because `_IS_BROWSER` is a runtime variable (not a
`TYPE_CHECKING` guard), the type checker analyses _both_ definitions.  Both
must have identical signatures.  The `# type: ignore[misc]` comment on the
browser overrides suppresses the "function already defined" lint, which is
expected and intentional here.

---

## 13. The `GameClient` API

`GameClient` is the public API that game code interacts with.  It owns a
`Transport` and provides a higher-level event-oriented interface.

### Connecting

```python
client = GameClient(host="ws://localhost:8765", nick="Player1")
await client.connect()
# Sends {"t": "hello", "nick": "Player1"} automatically on connect.
```

### Sending messages

All messages are JSON objects.  Use the typed helpers:

```python
client.send_join("lobby")          # {"t": "join", "room": "lobby"}
client.send_state({"x": 10})       # {"t": "state", "room": ..., "data": ...}
client.send_sync({"score": 42})    # {"t": "sync", "room": ..., "data": ...}
client.send_ping()                  # {"t": "ping"}
client.send({"t": "custom", ...})   # arbitrary message
```

### Receiving messages — event handlers

Register typed event handlers before connecting:

```python
def on_state(msg: JSON) -> None:
    print("got state:", msg["data"])

client.on("state", on_state)
```

Handlers are called synchronously inside `poll()`.

### Polling

`poll()` must be called regularly — it drains the transport's inbox, decodes
JSON, and dispatches to handlers.  Call it once per game frame:

```python
# In your game loop / step() method:
client.poll()
```

Or run the built-in async loop:

```python
asyncio.create_task(client.run())
# client.run() calls poll() every frame and exits when should_exit() is True.
```

### The inbox model

The transport accumulates incoming messages in `self.transport.inbox: list[str]`.
`poll()` pops one message per call.  If multiple messages arrive in one frame,
they will be processed on successive frames.  For high-frequency data this is
usually fine; for latency-sensitive state sync you may want to drain the entire
inbox per frame:

```python
def poll_all(client: GameClient) -> None:
    while True:
        data = client.transport.recv()
        if not data:
            break
        # ... parse and dispatch data
```

---

## 14. The `asyncio` Hijack

This is subtle and important to understand when debugging unexpected behaviour.

Inside the WASM runtime, `aio/__init__.py` ends with:

```python
sys.modules["asyncio"] = __import__(__name__)
```

After this executes, `import asyncio` anywhere in the codebase gives you `aio`,
not the standard library asyncio.  This means:

- `asyncio.sleep` is `aio.sleep` — same behaviour, different implementation.
- `asyncio.create_task` is `aio.create_task` — tracks tasks for cancellation.
- `asyncio.run` is `aio.run` — plugs into the frame scheduler, not blocking.

**Consequence**: do not rely on `asyncio.run()` doing a blocking loop in the
browser.  It registers the coroutine and returns.  The frame scheduler handles
advancing it.

**Debugging tip**: if you see `asyncio.something` behaving strangely in the
browser, check whether `aio` overrides it.  The source is at:

```
pygbag/support/cross/aio/__init__.py
```

in your uv cache at `.cache/uv/archive-v0/<hash>/pygbag/`.

---

## 15. Data Flow Reference

### Browser, JS WebSocket path (Path A)

```
Game code calls client.send(msg)
    → json.dumps(msg)
    → transport.send(str)
    → self._js_ws.send(str)          ← sync, returns None
    → browser WebSocket API
    → server

Server sends data
    → browser WebSocket API
    → on_message(event) callback     ← called by JS event loop
    → event.data (str or BinaryData)
    → self.inbox.append(str)         ← buffered

Game code calls client.poll()
    → transport.recv()
    → inbox.pop(0).encode("utf-8")   ← bytes to GameClient
    → json.loads(buffer)
    → client._emit(msg)
    → registered handlers called
```

### Browser, raw socket path (Path B)

```
Game code calls client.send(msg)
    → json.dumps(msg)
    → transport.send(str)
    → self.sock.send(bytes)          ← returns int (bytes written)
    → WASM socket bridge
    → JS WebSocket frame to port N+20000
    → pygbag proxy (strips WS framing)
    → TCP to server on port N

Server sends data
    → TCP from server
    → pygbag proxy (wraps in WS frame)
    → JS WebSocket frame
    → WASM socket bridge
    → _reader_browser() coroutine
        → select.select polls self.sock
        → self.sock.recv(4096)
        → data.decode("utf-8", "replace")
        → self.inbox.append(str)

Game code calls client.poll()
    → same as above from inbox.pop(0)
```

### Desktop, websockets path (Path C)

```
Game code calls client.send(msg)
    → json.dumps(msg)
    → transport.send(str)
    → run_task(self._desktop_ws.send(str))   ← schedules async send coroutine
    → asyncio event loop delivers bytes to server

Server sends data
    → asyncio event loop receives bytes
    → _reader_desktop() coroutine
        → async for msg in self._desktop_ws:
        → isinstance(msg, bytes): decode
        → self.inbox.append(str)

Game code calls client.poll()
    → same as above from inbox.pop(0)
```

---

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

### 8. The simulator does not emulate everything

The desktop pygbag simulator runs your code in a desktop Python process with a
simulated browser-like environment.  But it does not run a real browser, so:

- `js.WebSocket` may not be available or may behave differently.
- The port +20000 proxy is handled differently.
- Performance characteristics are completely different.

Always validate in a real browser before shipping.

---

## 17. Extending This Into the Engine

When the time comes to lift this networking code from the demo into the core
ajishio engine, here is what to consider:

### Stub file location

Move `js.pyi` and `aio/` (the stub package) out of `client/` and into the
engine's source tree or a dedicated `stubs/` directory.  Configure
basedpyright's `stubPath` in `pyproject.toml` so that all projects in the
workspace can find them:

```toml
[tool.basedpyright]
stubPath = "stubs"
```

Then move `stubs/js.pyi`, `stubs/aio/__init__.pyi`, `stubs/aio/cross.pyi`
there.

### Engine integration points

The three platform helpers (`should_exit`, `sleep0`, `run_task`) and the
`_IS_BROWSER` flag are the natural seam.  The engine already has a game loop;
the browser version needs to yield via `aio.sleep(0)` on every frame.  The
async game loop in `aj.async_game_start()` is already set up for this.

### Transport as an abstract interface

Consider extracting a `Protocol` that `Transport` (or its successors)
implement.  This would let the engine define the interface without depending
on the concrete implementation:

```python
class ITransport(Protocol):
    async def connect(self) -> None: ...
    def send(self, data: str) -> None: ...
    def recv(self) -> bytes | None: ...
    def close(self) -> None: ...
```

### The `GameClient` as an engine service

`GameClient` is essentially a service with a lifecycle (`connect`, `poll`,
`close`) and an event system.  This maps naturally onto an `aj.GameObject`
subclass (as demonstrated in `main.py`) or onto an engine-level service
registry if you build one.

### Framing and buffering

The current `inbox` model assumes one complete JSON object per recv call.  For
the engine, implement proper JSONL framing:  buffer incoming bytes, split on
`\n`, and only emit complete lines as messages.  This makes the transport
robust against partial recv and multi-message bursts.

---

*This document was written by inspecting the live pygbag 0.9.x source from
the uv package cache, the `pygbag_net.py` reference
