## 10. The Stub Files

Because `aio` and `js` are injected at runtime and have no installable Python
package, basedpyright cannot discover them from site-packages. This repository
provides dedicated stubs under `ajishio/typings`.

### How basedpyright finds them

The workspace config sets:

```toml
[tool.basedpyright]
stubPath = "ajishio/typings"
```

So these files are used globally:
- `ajishio/typings/js.pyi`
- `ajishio/typings/aio/__init__.pyi`
- `ajishio/typings/aio/cross.pyi`

### `ajishio/typings/js.pyi`

Documents the subset of the browser `window` global that this codebase uses:

- `js.WebSocket` — browser WebSocket class with event handlers and `send/close`.
- `js.Event` — the base event type passed to `onopen`, `onerror`, `onclose`.
  The `type: str` attribute gives the event type name.
- `js.MessageEvent` — `data` is `str | ArrayBuffer`.
- `js.eval(code: str) -> JSObject | JSFunction`.

The stub intentionally treats `ArrayBuffer` and `Uint8Array` as opaque. The
transport converts binary payloads via JS helpers rather than assuming
`.to_py()` support.

### `ajishio/typings/aio/__init__.pyi`

Documents the subset used by the transport:

- `aio.exit: bool` — the shutdown flag.  Poll in your main loop.
- `aio.sleep(delay: float) -> Awaitable[None]` — identical to `asyncio.sleep`.
- `aio.create_task(coro, ...) -> Task[T]` — identical to `asyncio.create_task`.
- `aio.cross` — re-exported from the `cross` submodule via relative import.

The relative import keeps resolution scoped to the local stub package.

### `ajishio/typings/aio/cross.pyi`

Minimal stub for the platform-detection submodule:

```python
simulator: bool
```

Runtime code still accesses it defensively via `getattr(..., "simulator", False)`.

### Maintaining the stubs

When using new `js.*` or `aio.*` members, update these stubs and verify against
runtime behavior in both desktop and browser paths.

---
