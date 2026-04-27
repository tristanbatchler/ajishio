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
This demo's server (`server/main.py`) is a `websockets.serve` WebSocket server,
so Path A is the primary connection method.  Path B (raw socket + proxy) is
only used as a fallback when `js.WebSocket` is unavailable (e.g., in the
pygbag desktop simulator).

---
