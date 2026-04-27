## 2. The Browser Runtime Environment

### `sys.platform`

Inside the WASM runtime, `sys.platform == "emscripten"`.  This is the single
most reliable way to detect you are running in the browser:

```python
_IS_BROWSER = sys.platform == "emscripten"
```

basedpyright does NOT narrow through this intermediate variable, so it always
analyses both branches.  This is intentional and important — it means the type
checker sees all code paths, which is what forces us to write fully typed,
platform-agnostic code.

### The event loop

The WASM asyncio loop is not driven by `asyncio.run()` in the normal sense.
Instead, pygbag replaces `asyncio` with its own `aio` module (see §3) and
drives the loop from a JavaScript `requestAnimationFrame` callback.

**Consequence**: you must `await` frequently.  Any synchronous code that runs
for more than ~16 ms will freeze the browser tab.  Every hot loop must contain
an `await sleep0()` (or equivalent) to yield control back to the browser.

### Sockets

WASM Python has a socket module, but the browser sandbox means raw TCP
connections are not possible.  Instead, pygbag provides a WebSocket-to-TCP
proxy bridge.  From Python, you use `socket.socket()` as normal; under the
hood, each connect/send/recv is tunnelled through a WebSocket connection managed
by JavaScript.  This is transparent to Python code but has consequences for
port numbers (see §8).

---
