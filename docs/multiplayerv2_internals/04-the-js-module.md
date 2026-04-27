## 4. The `js` Module

### What it is

`js` is a proxy to the browser's global JavaScript namespace.  Its source of
truth on Emscripten is a single line inside
`pygbag/support/cross/__EMSCRIPTEN__.py`:

```python
sys.modules["js"] = window.globalThis
```

`window.globalThis` is an Emscripten embed bridge object that reflects the
browser's `window` global.  Every property of `window` becomes an attribute of
the `js` module.  Every method of `window` becomes callable from Python.

### What this means in practice

```python
import js

# Read a browser global
origin = js.location.origin          # → "http://localhost:8000"

# Call a browser API
js.console.log("hello from Python")

# Evaluate arbitrary JavaScript
result = js.eval("1 + 1")            # → 2 (as a Python int proxy)

# Create a JS object
ws = js.eval(f"new WebSocket({url!r})")
```

`js.eval(code: str)` is the escape hatch for anything that the Emscripten
bridge does not expose as a direct attribute.  It evaluates `code` in the
browser's JS engine and returns the result as a Python proxy object.

### The `js.WebSocket` class

Because `js` mirrors `window`, and `window.WebSocket` is the browser's native
WebSocket class, `js.WebSocket` is the browser's WebSocket constructor.
However, creating a WebSocket via `js.WebSocket(url)` directly from Python
does not always work reliably across all pygbag versions.  The safe pattern
used in this codebase is:

```python
self._js_ws = cast(js.WebSocket, js.eval(f"new WebSocket({json.dumps(url)})"))
```

Using `json.dumps(url)` ensures the URL string is correctly quoted for
JavaScript, including handling special characters.

### JS objects from Python's perspective

A value returned from `js.eval()` is not a Python object — it is a _proxy_
that forwards attribute access and method calls to the underlying JavaScript
object.  The important things to know:

- **Attribute access** works normally: `ws.readyState`, `ws.binaryType`
- **Method calls** work normally: `ws.send("hello")`, `ws.close()`
- **Event handler assignment** works by Python assignment:
  `ws.onmessage = my_python_function` — pygbag wraps the Python callable in a
  JS function automatically.
- **Binary data** (e.g., an `ArrayBuffer` received over a binary WebSocket
  frame) arrives as a special proxy object, not as Python `bytes`.  You must
  call `.to_py()` on it to get a Python string.  This is why `on_message` in
  the transport contains the `isinstance(payload, str)` check.

### The `js` module on desktop

`js` does not exist on desktop.  It is only available inside the WASM runtime.
Attempting to `import js` on desktop raises `ModuleNotFoundError`.  This is
why every real import of `js` is either:

- Inside an `if _IS_BROWSER:` block, or
- Inside a `try: import js` block, or
- Under `if TYPE_CHECKING:` only (for type annotations — never executed).

---
