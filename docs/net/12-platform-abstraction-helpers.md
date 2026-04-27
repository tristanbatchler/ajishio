## 12. Platform Abstraction Helpers

Three module-level functions provide a platform-agnostic interface to the three
behaviours that differ between desktop and browser:

```python
def should_exit() -> bool: ...   # check if the app should quit
def sleep0() -> Awaitable[None]: ...  # yield for one event loop tick
def run_task(coro) -> Task[None]: ... # schedule a background coroutine
```

These are defined twice: first with `asyncio` defaults (desktop), then
overridden inside `if _IS_BROWSER:` with `aio`-based implementations:

```python
def should_exit() -> bool:
    return False                          # desktop: never exits via this flag

def should_exit() -> bool:               # browser override
    return aio.exit                       # browser: pygbag sets this on shutdown
```

basedpyright sees both definitions as having the same signature, so callers
are always type-safe regardless of which definition is active at runtime.

**Important**: because `_IS_BROWSER` is a runtime variable (not a
`TYPE_CHECKING` guard), the type checker analyses _both_ definitions.  Both
must have identical signatures.  The `# type: ignore[misc]` comment on the
browser overrides suppresses the "function already defined" lint, which is
expected and intentional here.

---
