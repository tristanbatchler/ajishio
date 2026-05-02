## 13. The `GameNetClient` API and `packets.py`

`GameNetClient` is a thin wrapper around `Transport`. The transport is protocol
agnostic; packet encoding/decoding lives in demo-level packet modules.

### API surface

```python
client = GameNetClient(host="ws://localhost:8765")
await client.connect()          # opens the transport connection

client.send(data: str | bytes)  # send raw payload
client.recv() -> bytes | None   # pop the next message, or None if inbox empty
await client.run()              # yield each frame; use as a background task
client.close()                  # close the connection
```

`client.connected` is `True` after `connect()` returns successfully.

### The `packets.py` pattern

In multiplayerv2, packets are frozen dataclasses with `encode() -> str` and a
top-level `decode(data: bytes) -> Packet | None` dispatcher.

```python
# demo_projects/multiplayerv2/shared/packets.py
@dataclass(frozen=True)
class Chat:
    sender_id: UUID
    text: str

    def encode(self) -> str:
        ...
```

Game code uses the two together:

```python
# Sending
client.send(Chat(sender_id=self.my_id, text=self.input_buffer).encode())

# Receiving — typically drain inbox each frame
raw = client.recv()
if raw is not None:
    pkt = decode(raw)
    if isinstance(pkt, Chat):
        self.message_log.append(pkt.text)
```

`recv()` returns `None` when the inbox is empty. Packet decoding is expected to
be resilient and return `None` for malformed/unknown payloads.

### Why `recv()` returns `bytes`

`Transport.inbox` stores bytes from all paths (desktop and browser), so callers
can decode with one code path regardless of transport backend.

`send()` accepts both `str` and `bytes`.  The multiplayerv2 demo intentionally
uses base64-encoded `str` packets for protocol portability and easy logging,
not because the transport requires string-only payloads.

### Background loop

```python
asyncio.create_task(client.run())
```

`run()` yields once per loop tick via `sleep0()` and exits when `should_exit()`
signals shutdown. It does not process messages; poll `recv()` in your game
loop.

---
