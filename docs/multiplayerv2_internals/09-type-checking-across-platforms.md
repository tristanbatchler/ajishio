## 9. Type Checking Across Platforms

### The challenge

The type checker (basedpyright) analyses all code paths simultaneously.  It
does not narrow based on `sys.platform == "emscripten"` when that check is
stored in an intermediate variable like `_IS_BROWSER`.  This means it sees
code that uses `js.WebSocket` AND code that uses
`websockets.ClientConnection` as potentially running in the same context.

### `TYPE_CHECKING` guard

The solution is the standard Python pattern:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import js                                          # never runs at runtime
    from websockets.asyncio.client import ClientConnection  # never runs at runtime
```

`TYPE_CHECKING` is always `False` at runtime and always `True` for the type
checker.  Code inside these blocks exists only for the benefit of the type
checker and never executes.  This allows us to write annotations that reference
`js.WebSocket` and `ClientConnection` without causing `ImportError` on
platforms where those modules don't exist.

### String annotations for inner-function forward references

Python 3.14 implements PEP 649 (lazy evaluation of annotations).  Function
parameter annotations are not evaluated when the function is defined — they are
only evaluated if something accesses `__annotations__`.  This means you can
safely write:

```python
def on_message(event: "js.MessageEvent") -> None:
    ...
```

inside a browser-only code block, even though `js` is not imported at runtime
on desktop.  The string `"js.MessageEvent"` is stored as a string, never
evaluated.  basedpyright resolves it using the `TYPE_CHECKING` import.

The quoted form is preferred over the bare form for browser-only types defined
in nested functions, because it makes the forward-reference intent explicit.

### `Coroutine[Any, Any, None]`

Real Python coroutines (from `async def f() -> None: ...`) have the type
`Coroutine[Any, Any, None]`.  The `Any` values represent the internal yield
and send types, which are implementation details of the coroutine machinery.
This is the correct and accurate type annotation for "a coroutine that returns
None", even though `reportExplicitAny` flags it.  The suppression comment:

```python
def run_task(coro: Coroutine[Any, Any, None]) -> Task[None]:  # pyright: ignore[reportExplicitAny]
```

is intentional and correct — not a hack.

### `cast()` for JS proxy objects

`js.eval(code)` returns `JSObject` (which is just `object` in the stubs —
the exact runtime type is unknowable statically).  When we know the returned
object is a `WebSocket`, we use `cast` to tell the type checker:

```python
self._js_ws = cast(js.WebSocket, js.eval(f"new WebSocket({json.dumps(url)})"))
```

`cast` has no runtime effect — it returns its second argument unchanged.  This
is safe because we are inside `if hasattr(js, "WebSocket"):` which guarantees
`js.WebSocket` exists, and `new WebSocket(url)` in JS is guaranteed to return
a `WebSocket` instance.

---
