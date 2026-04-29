from __future__ import annotations

from functools import lru_cache
from typing import Any

from anthropic import Anthropic, AsyncAnthropic

from app.config import get_settings


@lru_cache
def get_anthropic() -> AsyncAnthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


@lru_cache
def get_anthropic_sync() -> Anthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return Anthropic(api_key=settings.anthropic_api_key)


def default_model() -> str:
    return get_settings().anthropic_model


def judge_model() -> str:
    return get_settings().judge_model


def schema_to_tool(name: str, description: str, schema: type) -> dict[str, Any]:
    if hasattr(schema, "model_json_schema"):
        json_schema = schema.model_json_schema()
    else:
        raise TypeError(f"{schema!r} is not a Pydantic model")

    json_schema.pop("title", None)
    json_schema.pop("$defs", None)

    return {
        "name": name,
        "description": description,
        "input_schema": json_schema,
    }
