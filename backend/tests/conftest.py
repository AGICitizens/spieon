from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://spieon:spieon_dev_password_change_me@127.0.0.1:5432/spieon",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg://spieon:spieon_dev_password_change_me@127.0.0.1:5432/spieon",
)

from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from app import db as db_module
from app.main import app


@pytest.fixture(autouse=True)
def _reset_engine() -> Iterator[None]:
    db_module._engine = None
    db_module._sessionmaker = None
    yield
    db_module._engine = None
    db_module._sessionmaker = None


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
