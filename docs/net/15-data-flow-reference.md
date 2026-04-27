## 15. Data Flow Reference

### Browser, JS WebSocket path (Path A)

```
Game code calls client.send(ChatMessage(...).encode())
    → transport.send(str)
    → self._js_ws.send(str)          ← sync, JS handles async delivery
    → browser WebSocket API
    → server

Server sends data
    → browser WebSocket API
    → on_message(event) callback     ← fired by JS event loop
    → event.data: str or BinaryData proxy
    → str: inbox.append(str)
    → BinaryData: payload.to_py() → str or bytes → inbox.append(str)

Game code calls client.recv() in step()
    → transport.recv()
    → inbox.pop(0).encode("utf-8")   ← bytes returned to caller
    → caller: ChatMessage.decode(bytes) → ChatMessage | None
```

### Browser, raw socket path (Path B)

```
Game code calls client.send(ChatMessage(...).encode())
    → transport.send(str)
    → raw = str.encode("utf-8")
    → self.sock.send(raw)            ← returns int (bytes written)
    → WASM socket bridge
    → JS WebSocket frame to port N+20000
    → pygbag dev proxy (strips WS framing)
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

Game code calls client.recv() in step()
    → transport.recv()
    → inbox.pop(0).encode("utf-8")   ← bytes returned to caller
    → caller: ChatMessage.decode(bytes) → ChatMessage | None
```

### Desktop, websockets path (Path C)

```
Game code calls client.send(ChatMessage(...).encode())
    → transport.send(str)
    → run_task(self._desktop_ws.send(str))   ← schedules async coroutine
    → asyncio event loop delivers bytes to server

Server sends data
    → asyncio event loop receives bytes
    → _reader_desktop() coroutine
        → async for msg in self._desktop_ws:
        → isinstance(msg, bytes): decode to str
        → self.inbox.append(str)

Game code calls client.recv() in step()
    → transport.recv()
    → inbox.pop(0).encode("utf-8")   ← bytes returned to caller
    → caller: ChatMessage.decode(bytes) → ChatMessage | None
```

---
