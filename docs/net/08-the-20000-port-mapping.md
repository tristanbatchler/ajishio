## 8. The +20000 Port Mapping

This mapping applies only to the socket fallback path in browser mode.

### The problem

Browsers cannot make raw TCP connections — only WebSocket connections.
When Python code calls `socket.connect(("localhost", 8765))`, the WASM runtime
cannot literally open a TCP socket.  Instead, it sends a WebSocket connection
request to the pygbag development server.

### The solution

The pygbag dev server (`pygbag .`) exposes a WebSocket-to-TCP bridge used by
browser socket emulation.

In the current transport, for non-simulator fallback URLs, the mapped port is:

`mapped_port = original_port + 20000`

`ajishio/src/ajishio/net.py` applies this automatically:

```python
if not self.url.startswith("://"):
    port += 20000
```

The `"://"` format is used by simulator-specific addressing; in that case this
mapping is skipped.

### Practical implications

- This mapping is irrelevant for desktop mode.
- This mapping is irrelevant when browser JS WebSocket path is used.
- It only matters in browser fallback socket mode.

For this demo, the primary path is JS WebSocket. The fallback path exists for
compatibility but has stricter URL requirements and different runtime behavior.

---
