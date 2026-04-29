from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from app.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])

_client: Any | None = None
_initialized = False


def is_enabled() -> bool:
    settings = get_settings()
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def get_langfuse() -> Any | None:
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True
    if not is_enabled():
        return None

    from langfuse import Langfuse

    settings = get_settings()
    _client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    return _client


def flush() -> None:
    if _client is not None:
        try:
            _client.flush()
        except Exception:
            pass


def traced(name: str | None = None, *, kind: str = "span") -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        span_name = name or f"{fn.__module__}.{fn.__qualname__}"

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def aw(*args: Any, **kwargs: Any) -> Any:
                client = get_langfuse()
                if client is None:
                    return await fn(*args, **kwargs)
                start_ctx = (
                    client.start_as_current_generation
                    if kind == "generation"
                    else client.start_as_current_span
                )
                with start_ctx(name=span_name):
                    return await fn(*args, **kwargs)

            return aw  # type: ignore[return-value]

        @functools.wraps(fn)
        def w(*args: Any, **kwargs: Any) -> Any:
            client = get_langfuse()
            if client is None:
                return fn(*args, **kwargs)
            start_ctx = (
                client.start_as_current_generation
                if kind == "generation"
                else client.start_as_current_span
            )
            with start_ctx(name=span_name):
                return fn(*args, **kwargs)

        return w  # type: ignore[return-value]

    return decorator
