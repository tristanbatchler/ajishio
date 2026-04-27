# multiplayerv2

A minimal full-stack example of a Python client communicating with a
WebSocket server using JSON messages. Runs natively on desktop and
compiles to WebAssembly for the browser via pygbag — same codebase, no
source changes required.

---

## Project Structure

```
multiplayerv2/
├── client/
│   ├── main.py          Game entry point (pygame UI, keyboard input)
│   ├── net.py           Transport + GameClient (cross-platform networking)
│   ├── js.pyi           Type stub for the browser js module
│   └── aio/
│       ├── __init__.pyi Type stub for pygbag's aio runtime shim
│       └── cross.pyi    Type stub for aio.cross (platform detection)
└── server/
    └── main.py          asyncio WebSocket echo server
```

---

## Quick Start

### 1. Start the server

```bash
cd server
uv run main.py
```

Expected output:

```
websocket server on 0.0.0.0:8765
```

### 2a. Run the desktop client

```bash
cd client
uv run main.py
```

### 2b. Run the browser client

```bash
cd client
pygbag .
```

Then open `http://localhost:8000`.

---

## Expected Behaviour

Type letters and press Enter to send a message to the server. The server
echoes it back and it appears on screen.

### Server logs

```
SERVER DEBUG: connected ('127.0.0.1', 54252)
SERVER DEBUG: sent welcome
SERVER DEBUG: recv {'t': 'hello', 'nick': 'Player1'}
SERVER DEBUG: echoed message
SERVER DEBUG: recv {'t': 'message', 'text': 'hello'}
SERVER DEBUG: echoed message
```

### Client UI

```
Type something and press Enter to send it to the server.
Input: hello
Server: {"t": "welcome", "message": "Welcome to the echo server!"}
You: hello
Server: {"t": "echo", "data": {"t": "message", "text": "hello"}}
```

---

## Protocol

Messages are JSON objects sent over WebSocket frames. There is no
newline framing — each WebSocket frame carries exactly one JSON object.

```json
{"t": "hello",   "nick": "Player1"}
{"t": "message", "text": "hello"}
{"t": "ping"}
```

The server responds with:

```json
{"t": "welcome", "message": "Welcome to the echo server!"}
{"t": "echo",    "data": { ... }}
{"t": "error",   "message": "invalid json"}
```

---

## Transport

The transport layer (`net.py`) selects a connection strategy at runtime:

| Path | When | How |
|---|---|---|
| **A** — JS WebSocket | Browser, preferred | `js.eval("new WebSocket(url)")` via pygbag's injected `js` module |
| **B** — Raw socket | Browser, fallback | `socket.socket()` tunnelled through pygbag's WebSocket-to-TCP proxy on port +20000 |
| **C** — `websockets` | Desktop | `await websockets.connect(url)` via the `websockets` library |

All three paths funnel received messages into the same `inbox: list[str]`,
so `GameClient` is identical on every platform.

### The +20000 port mapping (Path B only)

When using the raw socket fallback in the browser, pygbag's dev server
proxies WebSocket connections on port `N+20000` to plain TCP on port `N`.
`net.py` applies this offset automatically. Path A (JS WebSocket) connects
directly to `ws://localhost:8765` and bypasses the proxy entirely.

---

## Components

### `GameClient` (`net.py`)

The public API for game code:

```python
client = GameClient(nick="Player1")
await client.connect()        # connects and sends hello

client.on("echo", handler)    # register an event handler
client.poll()                 # call once per frame to dispatch messages
client.send({"t": "ping"})    # send an arbitrary message
client.send_ping()            # convenience helpers
client.send_join("lobby")
client.send_state({...})
client.send_sync({...})
```

`poll()` must be called every frame. Without it no messages are processed
and no handlers fire.

### `Transport` (`net.py`)

Owned by `GameClient`. Manages the connection and `inbox`. Not intended
to be used directly by game code.

### Server (`server/main.py`)

A minimal `websockets.serve` echo server. On connect it sends a welcome
message, then echoes every subsequent message back as
`{"t": "echo", "data": <original>}`.

---

## Runtime Notes

The browser build uses two modules that pygbag injects at runtime —
`aio` (an asyncio shim) and `js` (a proxy to the browser's `window`
global). These have no PyPI equivalents and do not exist on desktop. The
`.pyi` stub files in `client/` teach the type checker about their
interfaces.

See [INTERNALS.md](INTERNALS.md) for a full technical reference covering
the injected modules, the three transport paths, the type-checking
setup, and known gotchas.

---

## Known Gotchas

**`poll()` is required.** The client is not purely event-driven. If you
forget to call `poll()` each frame, no messages are processed.

**One message per `recv()`.** The raw socket path reads up to 4096 bytes
per call with no JSONL framing. Large messages or message bursts can
cause parsing failures. Keep messages small.

**`on_message` callbacks must not `await`.** In the browser, JS event
callbacks fire synchronously between Python event loop ticks. Awaiting
inside them will raise a runtime error.

**Test in a real browser.** The desktop pygbag simulator does not fully
replicate the browser environment, particularly around WebSocket
availability and the port proxy.