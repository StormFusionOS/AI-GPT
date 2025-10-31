"""Ops API entrypoint."""
from __future__ import annotations

"""FastAPI application factory for the ops service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import alerts, auth, orchestrator, status
from ..automation import router as anomaly_router
from .core.config import get_settings
from .db import init_db
from ..orchestrator.health import run_health_checks


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.on_event("startup")
    async def startup() -> None:
        init_db()
        run_health_checks()

    prefix = settings.api_v1_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(status.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(orchestrator.router, prefix=prefix)
    app.include_router(anomaly_router, prefix=prefix)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
