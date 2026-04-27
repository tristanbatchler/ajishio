## 17. Extending This Into the Engine

When the time comes to lift this networking code from the demo into the core
ajishio engine, here is what to consider:

### Stub file location

Move `js.pyi` and `aio/` (the stub package) out of `client/` and into the
engine's source tree or a dedicated `stubs/` directory.  Configure
basedpyright's `stubPath` in `pyproject.toml` so that all projects in the
workspace can find them:

```toml
[tool.basedpyright]
stubPath = "stubs"
```

Then move `stubs/js.pyi`, `stubs/aio/__init__.pyi`, `stubs/aio/cross.pyi`
there.

### Engine integration points

The three platform helpers (`should_exit`, `sleep0`, `run_task`) and the
`_IS_BROWSER` flag are the natural seam.  The engine already has a game loop;
the browser version needs to yield via `aio.sleep(0)` on every frame.  The
async game loop in `aj.async_game_start()` is already set up for this.

### Transport as an abstract interface

Consider extracting a `Protocol` that `Transport` (or its successors)
implement.  This would let the engine define the interface without depending
on the concrete implementation:

```python
class ITransport(Protocol):
    async def connect(self) -> None: ...
    def send(self, data: str) -> None: ...
    def recv(self) -> bytes | None: ...
    def close(self) -> None: ...
```

### The `GameClient` as an engine service

`GameClient` is essentially a service with a lifecycle (`connect`, `poll`,
`close`) and an event system.  This maps naturally onto an `aj.GameObject`
subclass (as demonstrated in `main.py`) or onto an engine-level service
registry if you build one.

### Framing and buffering

The current `inbox` model assumes one complete JSON object per recv call.  For
the engine, implement proper JSONL framing:  buffer incoming bytes, split on
`\n`, and only emit complete lines as messages.  This makes the transport
robust against partial recv and multi-message bursts.

---

*This document was written by inspecting the live pygbag 0.9.x source from
the uv package cache, the `pygbag_net.py` reference
