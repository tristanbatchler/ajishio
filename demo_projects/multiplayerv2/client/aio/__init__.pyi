from collections.abc import Awaitable
import cross as cross

def sleep(delay: float) -> Awaitable[None]: ...

exit: bool

def run(coro: Awaitable[None]) -> None: ...
