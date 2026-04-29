from fastapi import APIRouter

from app.db import ping

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    db_ok = False
    error: str | None = None
    try:
        db_ok = await ping()
    except Exception as exc:
        error = str(exc)

    status = "ok" if db_ok else "degraded"
    payload: dict[str, object] = {"status": status, "db": db_ok}
    if error:
        payload["error"] = error
    return payload
