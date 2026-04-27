## 10. The Stub Files

Because `aio` and `js` are injected at runtime and have no installable Python
package, basedpyright cannot find them through normal module resolution.  We
provide hand-written stub files that teach the type checker about their
interfaces.

### How basedpyright finds them

basedpyright adds the directory of the file being analysed to its module search
path.  Since `net.py` lives in `client/`, the type checker looks in `client/`
for modules.  This is how:

- `client/js.pyi` is found when code does `import js`
- `client/aio/__init__.pyi` is found when code does `import aio`
- `client/aio/cross.pyi` is found when code does `import aio.cross` or
  accesses `aio.cross`

No `pyrightconfig.json` or `extraPaths` configuration is needed — the
co-location with `net.py` is enough.

### `client/js.pyi`

Documents the subset of the browser `window` global that this codebase uses:

- `js.WebSocket` — the browser WebSocket class.  `send()` accepts both `str`
  (text frame) and `bytes` (binary frame) — this has been verified at runtime
  through the Emscripten bridge.  `onopen`, `onmessage`, `onerror`, `onclose`
  are typed as nullable callable handlers; setting them to Python functions is
  how you register event listeners.
- `js.Event` — the base event type passed to `onopen`, `onerror`, `onclose`.
  The `type: str` attribute gives the event type name.
- `js.MessageEvent` — the event passed to `onmessage`.  The `data` attribute
  is either a plain `str` (text frames) or a `BinaryData` proxy (binary frames,
  i.e., ArrayBuffer).
- `js.MessageEvent.BinaryData` — the Pyodide proxy around a JS `ArrayBuffer`.
  Its only useful method from Python is `.to_py()`, which converts the buffer
  to a Python value.  In practice this returns either `str` or `bytes`
  depending on the frame content and pygbag version — the `on_message` handler
  checks both cases explicitly.
- `js.eval(code: str) -> JSObject` — the JS escape hatch.
- `JSObject = object` — used as a stand-in for the opaque proxy type.

### `client/aio/__init__.pyi`

Documents the parts of `aio` that differ from standard asyncio:

- `aio.exit: bool` — the shutdown flag.  Poll in your main loop.
- `aio.sleep(delay: float) -> Awaitable[None]` — identical to `asyncio.sleep`.
- `aio.create_task(coro, ...) -> Task[T]` — identical to `asyncio.create_task`.
- `aio.cross` — re-exported from the `cross` submodule.

The `from . import cross as cross` line uses a _relative_ import so that
basedpyright resolves `aio.cross` to `client/aio/cross.pyi`, not to a
hypothetical top-level `cross` module.

### `client/aio/cross.pyi`

Minimal stub for the platform-detection submodule:

```python
simulator: bool
```

In practice `simulator` can be `None` (unset) or `True`.  We declare it as
`bool` and access it defensively via `getattr(..., "simulator", False)` in
code, which short-circuits the type issue at the call site.

### Maintaining the stubs

When you discover new `js.*` or `aio.*` APIs you want to use, add them to the
appropriate stub file.  The golden rule: only add what you can verify by
inspecting the real runtime object.  Guessing leads to stubs that compile
cleanly but produce runtime errors.

---
