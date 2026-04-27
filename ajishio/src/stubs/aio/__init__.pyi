from asyncio import Task
from collections.abc import Awaitable
from contextvars import Context
from typing import TypeVar

from . import cross as cross

def sleep(delay: float) -> Awaitable[None]: ...

exit: bool

T = TypeVar("T")

def create_task(
    coro: Awaitable[T], *, name: str | None = None, context: Context | None = None
) -> Task[T]: ...
