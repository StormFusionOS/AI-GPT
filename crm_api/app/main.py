"""CRM API entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .api.routes import auth, leads, webhooks
from .core.config import get_settings
from .db import init_db
from .services.email_poller import EmailPoller

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(leads.router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(webhooks.router, prefix=f"{settings.api_v1_prefix}")

    poller = EmailPoller(
        interval_seconds=settings.email_poll_interval_seconds,
        sample_path=settings.email_poll_sample_path,
    )
    app.state.email_poller = poller

    if settings.email_poll_enabled:
        @app.on_event("startup")
        async def _start_email_poller() -> None:
            await poller.start()

        @app.on_event("shutdown")
        async def _stop_email_poller() -> None:
            await poller.stop()

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
