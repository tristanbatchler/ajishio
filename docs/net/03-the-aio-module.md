## 3. The `aio` Module

### What it is

`aio` is pygbag's custom async runtime shim.  Its source lives inside the
pygbag package at:

```
pygbag/support/cross/aio/__init__.py
```

It is injected at startup via:

```python
builtins.aio = sys.modules[__name__]  # inside aio/__init__.py
```

This means `aio` is available as a builtin — you can `import aio` from
anywhere inside the WASM runtime without it being a "real" installed package.

### What it contains

`aio` starts by doing `from asyncio import *`, which means it re-exports the
entire standard asyncio API.  It then overrides or augments specific pieces:

| Name | Type | Description |
|---|---|---|
| `aio.exit` | `bool` | Set to `True` by pygbag when the app should close.  Poll this in your main loop to know when to stop. |
| `aio.started` | `bool` | `True` once the event loop has been started. |
| `aio.paused` | `bool` | `True` when the loop is suspended (e.g., loading screen). |
| `aio.sleep(delay)` | `Awaitable[None]` | Identical to `asyncio.sleep`.  Yields control for at least `delay` seconds.  `aio.sleep(0)` yields for one frame. |
| `aio.create_task(coro)` | `Task[T]` | Identical to `asyncio.create_task`.  Schedules a coroutine on the running loop. |
| `aio.run(coro)` | `None` | Like `asyncio.run`, but plugs into the frame-based scheduler instead of blocking. |
| `aio.loop` | `AbstractEventLoop` | The single shared event loop for the WASM runtime. |
| `aio.cross` | module | Platform-detection submodule (see §5). |

### The `from asyncio import *` trick

Because `aio` re-exports all of `asyncio`, code that did `import asyncio` and
then uses `asyncio.sleep`, `asyncio.create_task` etc. will _mostly_ work even
in the browser — because at module-level, `sys.modules["asyncio"] = aio`.
That line is the last thing `aio/__init__.py` does:

```python
sys.modules["asyncio"] = __import__(__name__)
```

So after `aio` loads, `import asyncio` gives you `aio`.  This is why the same
`asyncio.sleep(0)` call works on both desktop and browser — on browser it's
actually `aio.sleep(0)` in disguise.

### Why we don't just use `asyncio` everywhere

The important divergences are:

- `aio.exit` — no equivalent in real asyncio.
- `aio.create_task` stores created tasks in an internal list so pygbag can
  cancel them on shutdown.  Real `asyncio.create_task` does not.
- `aio.sleep(0)` advances the _frame-based_ loop; `asyncio.sleep(0)` on
  desktop advances the _I/O-based_ loop.  The effect is the same for our
  purposes, but the implementation path is different.

Using the `aio.*` names directly (instead of relying on the `sys.modules`
hijack) is more explicit and makes the browser-specific intent clear.

---
