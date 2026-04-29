from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.store.postgres import AsyncPostgresStore
from langgraph.store.postgres.base import PostgresIndexConfig

from app.config import get_settings
from app.models.memory import EMBEDDING_DIM

EMBEDDING_MODEL = "openai:text-embedding-3-small"
PROCEDURAL_NAMESPACE = ("spieon", "procedural")


def procedural_namespace(target_type: str | None = None) -> tuple[str, ...]:
    if target_type:
        return (*PROCEDURAL_NAMESPACE, target_type)
    return PROCEDURAL_NAMESPACE


def _index_config() -> PostgresIndexConfig:
    return PostgresIndexConfig(
        dims=EMBEDDING_DIM,
        embed=EMBEDDING_MODEL,
        distance_type="cosine",
    )


def _psycopg_dsn() -> str:
    sync_url = get_settings().database_url_sync
    return sync_url.replace("postgresql+psycopg://", "postgresql://", 1)


@asynccontextmanager
async def get_store(*, with_index: bool = True) -> AsyncIterator[AsyncPostgresStore]:
    dsn = _psycopg_dsn()
    index = _index_config() if with_index else None
    async with AsyncPostgresStore.from_conn_string(dsn, index=index) as store:
        yield store


async def setup_store(*, with_index: bool = True) -> None:
    async with get_store(with_index=with_index) as store:
        await store.setup()
