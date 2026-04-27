## 13. The `GameClient` API and `packets.py`

`GameClient` is a thin, protocol-agnostic wrapper around `Transport`.  It
sends and receives raw strings only.  All encoding and decoding of packet
contents is the responsibility of the caller — deliberately kept out of the
transport layer so that the wire format can change without touching `net.py`.

### API surface

```python
client = GameClient(host="ws://localhost:8765")
await client.connect()          # opens the transport connection

client.send(data: str)          # send a raw encoded string
client.recv() -> bytes | None   # pop the next message, or None if inbox empty
await client.run()              # yield each frame; use as a background task
client.close()                  # close the connection
```

`client.connected` is `True` after `connect()` returns successfully.

### The `packets.py` pattern

All wire-format decisions live in `packets.py`, not in `net.py` or game code.
Each packet type is a frozen dataclass with `encode() -> str` and a
`@classmethod decode(bytes) -> T | None`:

```python
# packets.py
@dataclass(frozen=True)
class ChatMessage:
    text: str

    def encode(self) -> str:
        return json.dumps({"t": "chat", "text": self.text})

    @classmethod
    def decode(cls, data: bytes) -> "ChatMessage | None":
        ...  # returns None on any parse error, never raises
```

Game code uses the two together:

```python
# Sending
client.send(ChatMessage(text=self.input_buffer).encode())

# Receiving — call once per frame in step()
raw = client.recv()
if raw:
    msg = ChatMessage.decode(raw)
    if msg:
        self.message_log.append(msg.text)
```

`recv()` returns `None` when the inbox is empty, so the `if raw:` guard is
sufficient.  `ChatMessage.decode` returns `None` for anything that is not a
valid chat packet, so unknown message types are silently ignored without
raising exceptions.

### Why `recv()` returns `bytes`

`Transport.inbox` stores decoded `str` values.  `recv()` re-encodes them to
`bytes` (via `.encode("utf-8")`) so that callers always receive a consistent
`bytes | None` type regardless of transport path — keeping the API stable even
if the underlying inbox representation changes.

### Background loop

```python
asyncio.create_task(client.run())
```

`run()` is a coroutine that yields once per event loop tick via `sleep0()` and
exits when `should_exit()` returns `True`.  It does no message processing —
call `client.recv()` yourself in `step()` rather than relying on a background
loop for message delivery.

---
