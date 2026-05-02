## 12. Platform Abstraction Helpers

Three module-level functions provide a platform-agnostic seam for runtime
differences between desktop and browser:

```python
def should_exit() -> bool: ...   # check if the app should quit
def sleep0() -> Awaitable[None]: ...  # yield for one event loop tick
def run_task(coro) -> Task[None]: ... # schedule a background coroutine
```

They are defined with asyncio defaults, then replaced inside `if _IS_BROWSER:`
with `aio` implementations:

```python
def should_exit() -> bool:
    return False                          # desktop: never exits via this flag

def should_exit() -> bool:               # browser override
    return aio.exit                       # browser: pygbag sets this on shutdown
```

Both versions keep identical signatures so call sites remain typed uniformly.

**Important**: `_IS_BROWSER` is runtime-only, so static analysis sees both
branches. Keep signatures aligned and keep behavior minimal in these helpers.

---
