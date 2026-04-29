from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, scans, ws
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Spieon", version="0.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(scans.router)
    app.include_router(ws.router)
    return app


app = create_app()
