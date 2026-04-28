# multiplayerv2

A minimal full-stack chatroom demo: multiple Python clients can connect and
chat with each other in real time. Runs natively on desktop and compiles to
WebAssembly for the browser via pygbag — same codebase, no source changes
required.

Uses a **binary packet protocol** (struct-packed, base64-encoded for
transport) instead of JSON. Sender identity is a UUID assigned by the server.

---

## Project Structure

```
multiplayerv2/
├── client/
│   ├── main.py          Chatroom UI (pygame, keyboard input)
│   ├── packets.py       Binary wire-format codec (shared by server)
│   └── CutiveMono-Regular.ttf
└── server/
    └── main.py          asyncio WebSocket server with ID assignment
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

On connect, the server assigns you a UUID (the first 8 hex chars are shown
in the title bar). A ping/pong round-trip is measured and displayed.
Join/leave notifications appear for other clients.

Type letters and press Enter to send a chat message. It is broadcast to
all connected clients. Messages appear prefixed with the sender's short ID.

Keys accepted: `a–z`, `0–9`, space, `! ? . , ' -`
Backspace deletes the last character.

### Server logs

```
SERVER: connected ('127.0.0.1', 54321) as a1b2c3d4, total=1
SERVER: ping from a1b2c3d4 token=12345678
SERVER: chat from a1b2c3d4: 'hello'
SERVER: disconnected a1b2c3d4 ('127.0.0.1', 54321), total=0
```

### Client UI

```
Ajishio Chat Demo  (a1b2c3d4)
* connected as a1b2c3d4          ← green
* pong: 2 ms                     ← gray
+ e5f6a7b8 joined                ← green
[a1b2c3d4] hello                 ← aqua (own messages)
[e5f6a7b8] world                 ← white (others)
- e5f6a7b8 left                  ← orange
> _
```

---

## Protocol

Each message is a single base64-encoded binary blob sent in one WebSocket
text frame. Base64 is used because `GameNetClient.send()` accepts `str`
only and the transport inbox round-trips through UTF-8.

### Binary layout

```
[1 byte: PacketType tag] [N bytes: body]
```

### Packet types

| Tag | Name               | Direction         | Body                            |
|-----|--------------------|-------------------|---------------------------------|
| 0   | AssignId           | server → client   | `!16s` sender UUID              |
| 1   | Chat               | client ↔ server   | `!16s` sender UUID + UTF-8 text |
| 2   | Ping               | client → server   | `!16sI` sender UUID + token     |
| 3   | Pong               | server → client   | `!I` token                      |
| 4   | ClientConnected    | server → clients  | `!16s` new client UUID          |
| 5   | ClientDisconnected | server → clients  | `!16s` departed client UUID     |

The server re-encodes Chat packets with the verified sender_id before
broadcasting, so clients cannot spoof their identity.

### Extensibility

To add a new packet type (e.g. Whisper, Poke):

1. Add an entry to `PacketType` in `packets.py`.
2. Create a frozen dataclass with `encode() -> str` and
   `@staticmethod unpack_body(body: bytes) -> Self | None`.
3. Register it in `_REGISTRY`.
4. Handle it in the server and/or client.

---

## Architecture

### Transport layer (`ajishio.net`)

The engine's `GameNetClient` is protocol-agnostic. It moves raw `str`
between client and server. See the engine docs for connection strategy
details (JS WebSocket / raw socket fallback / desktop websockets).

### Packet layer (`packets.py`)

All wire-format decisions live here. Packets are frozen dataclasses that
`struct.pack` their fields into binary, then base64-encode for transport.
`decode(data: bytes) -> Packet | None` dispatches on the type tag byte
and never raises.

### Server (`server/main.py`)

A `websockets.serve` server that:

- Assigns each client a UUID via `uuid4()` on connect.
- Sends an `AssignId` packet as the first message.
- Broadcasts `ClientConnected` to all other clients.
- Decodes incoming packets and dispatches by type.
- Re-stamps Chat packets with the verified sender_id before broadcast.
- Responds to Ping with Pong.
- Broadcasts `ClientDisconnected` on disconnect.

### Client (`client/main.py`)

An `aj.GameObject` subclass that:

- Waits for `AssignId` as the first packet from the server.
- Sends a `Ping` immediately after receiving its ID.
- Accepts keyboard input and sends `Chat` packets.
- Drains all queued packets each frame (not just one).
- Displays messages in color: aqua for own, white for others, green for
  joins, orange for leaves, gray for system info.

---

## Known Gotchas

**`recv()` returns one message per call.** The client drains in a
`while` loop each frame to handle bursts.

**Base64 overhead.** Each packet is ~33% larger on the wire than raw
binary. This is acceptable for a chat demo; a production game would
modify `GameNetClient.send()` to accept `bytes` directly.
