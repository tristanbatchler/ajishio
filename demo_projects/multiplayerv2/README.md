# multiplayerv2

A minimal full-stack chatroom demo: multiple Python clients can connect and
chat with each other in real time. Runs natively on desktop and compiles to
WebAssembly for the browser via pygbag — same codebase, no source changes
required.

---

## Project Structure

```
multiplayerv2/
├── client/
│   ├── main.py          Chatroom UI (pygame, keyboard input)
│   ├── net.py           Transport + GameClient (cross-platform networking)
│   ├── packets.py       Wire-format codec (ChatMessage encode/decode)
│   ├── js.pyi           Type stub for the browser js module
│   └── aio/
│       ├── __init__.pyi Type stub for pygbag's aio runtime shim
│       └── cross.pyi    Type stub for aio.cross (platform detection)
└── server/
    └── main.py          asyncio WebSocket broadcast server
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
chat server on 0.0.0.0:8765
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

Open multiple clients to see messages broadcast between them.

---

## Expected Behaviour

Type letters and press Enter to send a chat message. It is broadcast to
all connected clients, including yourself — your own message appears in
the log when it comes back from the server.

Keys accepted: `a–z`, `0–9`, space, `! ? . , ' -`
Backspace deletes the last character.

### Server logs

```
SERVER: connected ('127.0.0.1', 54321), total=1
SERVER: recv from ('127.0.0.1', 54321): '{"t": "chat", "text": "hello"}'
SERVER: disconnected ('127.0.0.1', 54321), total=0
```

### Client UI

```
Chatroom — type and press Enter to send
> hello_
hello
world
```

---

## Protocol

Each message is a single JSON object sent in one WebSocket frame.
There is no newline framing — one frame, one object.

### Client → Server

```json
{"t": "chat", "text": "hello"}
```

### Server → all clients (including sender)

```json
{"t": "chat", "text": "hello"}
```

The server relays messages without parsing them. `packets.py` on the
client side is responsible for encoding and decoding.

---

## Architecture

### Transport layer (`net.py`)

`net.py` is protocol-agnostic. It moves raw `str`/`bytes` between the
client and server without knowing anything about packet structure.

Connection strategy selected at runtime:

| Path | When | How |
|---|---|---|
| **A** — JS WebSocket | Browser, preferred | `js.eval("new WebSocket(url)")` via pygbag's injected `js` module |
| **B** — Raw socket | Browser, fallback | `socket.socket()` tunnelled through pygbag's WebSocket-to-TCP proxy on port +20000 |
| **C** — `websockets` | Desktop | `await websockets.connect(url)` via the `websockets` library |

All three paths funnel received messages into `inbox: list[str]`, so
`GameClient` behaves identically on every platform.

### Packet layer (`packets.py`)

All wire-format decisions live here. Each packet type is a frozen
dataclass with `encode() -> str` and `decode(bytes) -> T | None`.
`decode` returns `None` on any error and never raises.

### `GameClient` (`net.py`)

Thin wrapper around `Transport`. The full API:

```python
client = GameClient(host="ws://localhost:8765")
await client.connect()

client.send(data: str)        # send a raw encoded string
client.recv() -> bytes | None # pop the next message, or None
await client.run()            # yield each frame (use as background task)
client.close()
```

### Server (`server/main.py`)

A `websockets.serve` broadcast server. Every received message is relayed
verbatim to all connected clients including the sender. The server does
not parse JSON.

---

## Runtime Notes

The browser build relies on two modules that pygbag injects at runtime:

- `aio` — an asyncio shim that drives the event loop via
  `requestAnimationFrame` instead of blocking I/O
- `js` — a proxy to the browser's `window` global, giving Python access
  to the native WebSocket API

Neither module exists on desktop or on PyPI. The `.pyi` stub files in
`client/` teach the type checker about their interfaces.

See [INTERNALS.md](INTERNALS.md) for a full technical reference.

---

## Known Gotchas

**`recv()` returns one message per call.** Call it every frame in
`step()`. If multiple messages arrive in one frame they queue up in
`inbox` and are delivered on successive frames.

**Do not `await` inside JS event callbacks.** `on_message`, `on_open`,
`on_error`, and `on_close` fire synchronously between Python event loop
ticks. Awaiting inside them will raise a runtime error.

**Keep strong references to callbacks.** When assigning Python functions
to `js.WebSocket` event properties, JavaScript receives a proxy wrapper.
If Python garbage-collects the original callable, the proxy becomes a
dangling pointer and callbacks silently stop firing. Always store the
functions on `self` before assigning them to the socket. See §11 of
INTERNALS.md for the full explanation.

**Test in a real browser.** The desktop pygbag simulator does not fully
replicate the browser environment, particularly around WebSocket
availability and the +20000 port proxy.