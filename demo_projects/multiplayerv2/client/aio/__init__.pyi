from collections.abc import Awaitable
from typing import TypeVar
import cross as cross
from asyncio import Task
from contextvars import Context

def sleep(delay: float) -> Awaitable[None]: ...

exit: bool

T = TypeVar("T")

def create_task(
    coro: Awaitable[T], *, name: str | None = None, context: Context | None = None
) -> Task[T]: ...
