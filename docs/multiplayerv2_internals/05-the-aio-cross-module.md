## 5. The `aio.cross` Module

### What it is

`aio.cross` is a submodule of `aio` that holds platform-detection state.  Its
source is at `pygbag/support/cross/aio/cross.py`.

### Key attributes

| Name | Type | Default | Meaning |
|---|---|---|---|
| `aio.cross.simulator` | `bool \| None` | `None` | `True` when running in the pygbag desktop simulator (see §6).  `None` or `False` when running in a real browser or on desktop. |
| `aio.cross.scheduler` | `callable \| None` | `None` | The function pygbag uses to reschedule the event loop step.  Internal use only. |

### Why we care about `simulator`

The simulator and the real browser handle WebSocket/socket connections
differently — particularly the URL format.  In the simulator, the server
address is embedded in the URL _path_ in a special format, rather than being a
plain `host:port` pair.  The `aio_sock_open` function in `net.py` checks this:

```python
if getattr(aio.cross, "simulator", False):
    if "/" in host:
        host, trail = host.strip(":/").split("/", 1)
        port = int(trail.rsplit(":", 1)[-1])
```

We use `getattr(..., "simulator", False)` as a defensive call because `aio` is
only available in the browser, and `aio.cross.simulator` could theoretically be
`None` rather than `False` in some contexts.

---
