## 6. The Simulator vs Real Browser

pygbag has two runtime modes:

### Real browser (Emscripten, `sys.platform == "emscripten"`)

- CPython compiled to WASM runs inside a browser tab.
- `js` module is the real `window.globalThis`.
- `js.WebSocket` is the real browser WebSocket API.
- Network connections go through the browser's network stack.
- `aio.cross.simulator` is `None` / falsy.

### Desktop simulator (`pygbag.aio`, non-emscripten)

- pygbag provides a Python-side simulation of the WASM environment that runs
  on your normal desktop Python.
- Useful for iteration without having to compile to WASM.
- `aio` is still injected (via `pygbag/aio.py` which imports the support
  module and runs a desktop event loop).
- `js` is injected differently — the desktop simulator uses a stub.
- Socket connections use a different URL encoding format.
- `aio.cross.simulator` is `True`.

### What this means for you

When testing networking locally, you may find yourself in the simulator.

In this repository's current `Transport` implementation, simulator-specific
`aio.cross.simulator` logic is only used in the browser fallback path.  The
desktop simulator path (`_IS_BROWSER == False`) goes through desktop
`websockets.connect(...)`.

Always test in a real browser before assuming simulator behaviour matches
production.

---
