## 15. Data Flow Reference

### Browser, JS WebSocket path

```
Game code calls client.send(Packet(...).encode())
    → transport.send(str)
    → self._js_ws.send(str)          ← sync, JS handles async delivery
    → browser WebSocket API
    → server

Server sends data
    → browser WebSocket API
    → on_message(event) callback
    → event.data: str or ArrayBuffer
    → str: inbox.append(str.encode("utf-8"))
    → ArrayBuffer: convert via Uint8Array helper → inbox.append(bytes)

Game code calls client.recv() in step()
    → transport.recv()
    → inbox.pop(0)                    ← bytes returned to caller
    → caller: decode(bytes) → Packet | None
```

### Browser, socket fallback path

```
Game code calls client.send(Packet(...).encode())
    → transport.send(str)
    → raw = str.encode("utf-8")
    → self.sock.send(raw)            ← returns int (bytes written)
    → WASM socket bridge / pygbag proxy path

Server sends data
    → TCP from server
    → pygbag proxy (wraps in WS frame)
    → JS WebSocket frame
    → WASM socket bridge
    → _reader_browser() coroutine
        → select.select polls self.sock
        → self.sock.recv(4096)
        → self.inbox.append(data)

Game code calls client.recv() in step()
    → transport.recv()
    → inbox.pop(0)                    ← bytes returned to caller
    → caller: decode(bytes) → Packet | None
```

### Desktop, websockets path

```
Game code calls client.send(Packet(...).encode())
    → transport.send(str)
    → run_task(self._desktop_ws.send(str))   ← schedules async coroutine
    → asyncio event loop delivers bytes to server

Server sends data
    → asyncio event loop receives bytes
    → _reader_desktop() coroutine
        → async for msg in self._desktop_ws:
        → bytes: inbox.append(msg)
        → str: inbox.append(msg.encode("utf-8"))

Game code calls client.recv() in step()
    → transport.recv()
    → inbox.pop(0)                    ← bytes returned to caller
    → caller: decode(bytes) → Packet | None
```

---
