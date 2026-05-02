## 17. Extending This Into the Engine

This networking layer already lives in the engine (`ajishio/src/ajishio/net.py`)
and is exposed as `aj.GameNetClient`. This page focuses on future evolution.

### Stub maintenance

Keep stubs in `ajishio/typings` in sync with runtime usage in `net.py`.
Current workspace configuration already points basedpyright there:

```toml
[tool.basedpyright]
stubPath = "ajishio/typings"
```

### Engine integration points

The three platform helpers (`should_exit`, `sleep0`, `run_task`) and the
`_IS_BROWSER` flag are the natural seam.  The engine already has a game loop;
the browser version needs to yield via `aio.sleep(0)` on every frame.  The
async game loop in `aj.async_game_start()` is already set up for this.

### Optional transport abstraction

Consider extracting a `Protocol` that `Transport` (or its successors)
implement.  This would let the engine define the interface without depending
on the concrete implementation:

```python
class ITransport(Protocol):
    async def connect(self) -> None: ...
    def send(self, data: str | bytes) -> None: ...
    def recv(self) -> bytes | None: ...
    def close(self) -> None: ...
```

### `GameNetClient` as an engine service

`GameNetClient` is a service with a lifecycle (`connect`, `poll`, `close`).
It maps naturally onto an `aj.GameObject`
subclass (as demonstrated in `main.py`) or onto an engine-level service
registry if you build one.

### Framing and buffering improvements

If you need strict packet boundaries in fallback mode, add optional framing at
the protocol layer (for example length-prefix framing or newline-delimited
messages) and decode incrementally.

---
