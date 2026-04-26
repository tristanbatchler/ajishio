# pygame-browser-socket-demo

A minimal full-stack example of a **Python (pygbag) browser client** communicating with a **custom asyncio TCP server** using a simple JSONL protocol.

This project demonstrates how to build multiplayer networking in the browser without WebSockets, using raw TCP sockets bridged through `pygbag`.

---

## 🧠 What This Project Is

This is a **browser-native Python networking experiment**:

* Python compiled to WebAssembly (via `pygbag`)
* Raw TCP connection from the browser
* JSONL (newline-delimited JSON) protocol
* Minimal asyncio server backend

It is intentionally small, low-level, and hackable.

---

## ⚠️ Key Constraint (Read This First)

### This is NOT WebSockets

Even though it runs in a browser:

* ❌ No `ws://`
* ❌ No WebSocket upgrade handshake
* ❌ No browser WebSocket API usage

Instead:

```
pygbag_net → aio_sock → raw TCP socket → asyncio server
```

### Your server must:

* Be a plain TCP server
* Accept newline-delimited JSON messages (`\n`)
* Ignore binary/TLS noise safely
* Never assume perfect message framing

---

## ⚠️ Runtime Abstraction Layer

This project intentionally avoids depending on `pygbag` internals.

* `asyncio` is the scheduling model and event loop semantics
* `aio` is a platform compatibility shim for browser or desktop runtimes
* `GameClient` and the transport layer are runtime-agnostic
* `pygbag.aio` is not part of the public architecture and should be avoided in application logic

---

## 📁 Project Structure

```
client/   → pygbag browser client (WASM Python)
server/   → asyncio TCP JSONL server
```

---

## 🚀 Quick Start

### 1. Start the server

```bash
cd server
uv run main.py
```

Expected output:

```
echo server on 0.0.0.0:8765
```

---

### 2. Start the browser client

```bash
cd client
pygbag .
```

Then open:

```
http://localhost:8000
```

---

## 🧪 Expected Behaviour

When working correctly:

### Server logs:

```
connected: ('127.0.0.1', 54252)
recv: {'t': 'hello', 'nick': 'u_12345'}
```

### Client logs:

```
CONNECTED: {'t': 'connected', 'nick': 'u_12345'}
JOINED: lobby
STATE: {...}
SYNC: {...}
```

---

## 🔌 Protocol Overview

All communication uses **JSONL over TCP**:

* One JSON object per line
* UTF-8 encoding
* `\n` terminated messages

### Example message

```json
{"t":"state","room":"lobby","data":{"x":10,"y":20}}
```

---

## 🧩 Components

### Client (pygbag)

Runs in the browser:

* Uses `GameClient`
* Handles socket buffering
* Emits event-based messages (`state`, `sync`, etc.)
* Runs in a cooperative async loop

---

### Transport Layer (`pygbag_net`)

Handles:

* raw socket connection
* buffering partial TCP frames
* JSON decoding
* newline framing
* event dispatch

---

### Server (asyncio TCP)

Minimal backend:

* Accepts TCP connections
* Reads JSONL messages
* Echoes or broadcasts data
* No game logic required

---

## 🔁 Data Flow

```
Browser (pygbag)
      ↓
GameClient
      ↓
Transport (aio_sock)
      ↓
TCP socket stream
      ↓
Asyncio server
```

---

## 🧠 Design Philosophy

This project intentionally avoids “modern abstractions”:

* No WebSockets
* No RPC frameworks
* No binary protocols
* No dependency-heavy networking stacks

Instead:

> raw TCP + JSONL + event loop = predictable browser networking

---

## ⚠️ Known Gotchas

### 1. Binary noise is normal

You may see:

```
BINARY: 16030106c6...
```

This is:

* TLS probes
* browser networking artifacts
* partial socket data

Ignore it safely.

---

### 2. You MUST use JSONL

Every message must end in:

```
\n
```

Without it:

* messages merge
* client buffers stall
* events break silently

---

### 3. You must call `poll()`

The client is not fully async-driven.

If you don’t poll:

* no messages are processed
* events stop entirely

---

### 4. This is not a reliable transport

Expect:

* partial packets
* merged frames
* delayed delivery
* occasional disconnects

This is normal for browser sockets.

---

## 🔜 Where This Goes Next

This repo is the foundation for a real multiplayer system.

Possible extensions:

* room-based routing
* authoritative server state
* input prediction
* delta sync / snapshots
* compression layer
* reconnect + resync logic

---

## 🧪 Why This Exists

Because in `pygbag`:

> networking is not “plug and play WebSockets” — it’s a constrained TCP emulation layer

This project shows the **smallest working end-to-end loop** between:

* browser Python
* raw sockets
* asyncio server
* structured game messages
