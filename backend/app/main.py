from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    agent,
    erc8004,
    findings,
    health,
    keeperhub,
    memory,
    modules,
    payouts,
    scans,
    ws,
)
from app.config import get_settings
from app.lifespan import lifespan


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Spieon", version="0.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(scans.router)
    app.include_router(findings.router)
    app.include_router(payouts.router)
    app.include_router(modules.router)
    app.include_router(memory.router)
    app.include_router(agent.router)
    app.include_router(erc8004.router)
    app.include_router(keeperhub.router)
    app.include_router(ws.router)
    return app


app = create_app()
