from __future__ import annotations

from functools import lru_cache
from typing import Any

from openai import AsyncOpenAI, OpenAI

from app.config import get_settings


@lru_cache
def get_openrouter() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


@lru_cache
def get_openrouter_sync() -> OpenAI:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


@lru_cache
def get_zerog_compute() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.zerog_compute_api_key:
        raise RuntimeError("ZEROG_COMPUTE_API_KEY is not set")
    return AsyncOpenAI(
        api_key=settings.zerog_compute_api_key,
        base_url=settings.zerog_compute_base_url,
    )


def llm_provider() -> str:
    """Return the active provider id: '0g-compute' if a 0G key is configured, else 'openrouter'."""
    return "0g-compute" if get_settings().zerog_compute_api_key else "openrouter"


def has_llm() -> bool:
    s = get_settings()
    return bool(s.zerog_compute_api_key or s.openrouter_api_key)


def chat_client() -> AsyncOpenAI:
    """Return the active LLM client. Prefers 0G Compute when configured."""
    if get_settings().zerog_compute_api_key:
        return get_zerog_compute()
    return get_openrouter()


def default_model() -> str:
    s = get_settings()
    if s.zerog_compute_api_key:
        return s.zerog_compute_model or s.openrouter_model
    return s.openrouter_model


def judge_model() -> str:
    s = get_settings()
    if s.zerog_compute_api_key:
        return s.zerog_compute_judge_model or s.zerog_compute_model or s.judge_model
    return s.judge_model


def schema_to_tool(name: str, description: str, schema: type) -> dict[str, Any]:
    if hasattr(schema, "model_json_schema"):
        json_schema = schema.model_json_schema()
    else:
        raise TypeError(f"{schema!r} is not a Pydantic model")

    json_schema.pop("title", None)
    json_schema.pop("$defs", None)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": json_schema,
        },
    }
