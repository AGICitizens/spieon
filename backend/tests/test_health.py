from __future__ import annotations

from httpx import AsyncClient


async def test_health_reports_db_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] is True


async def test_health_degrades_when_db_unreachable(
    client: AsyncClient, monkeypatch
) -> None:
    from app.api import health as health_module

    async def boom() -> bool:
        raise RuntimeError("connection refused")

    monkeypatch.setattr(health_module, "ping", boom)

    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] is False
    assert "connection refused" in body["error"]
