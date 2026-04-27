## 14. The `asyncio` Hijack

This is subtle and important to understand when debugging unexpected behaviour.

Inside the WASM runtime, `aio/__init__.py` ends with:

```python
sys.modules["asyncio"] = __import__(__name__)
```

After this executes, `import asyncio` anywhere in the codebase gives you `aio`,
not the standard library asyncio.  This means:

- `asyncio.sleep` is `aio.sleep` — same behaviour, different implementation.
- `asyncio.create_task` is `aio.create_task` — tracks tasks for cancellation.
- `asyncio.run` is `aio.run` — plugs into the frame scheduler, not blocking.

**Consequence**: do not rely on `asyncio.run()` doing a blocking loop in the
browser.  It registers the coroutine and returns.  The frame scheduler handles
advancing it.

**Debugging tip**: if you see `asyncio.something` behaving strangely in the
browser, check whether `aio` overrides it.  The source is at:

```
pygbag/support/cross/aio/__init__.py
```

in your uv cache at `.cache/uv/archive-v0/<hash>/pygbag/`.

---
