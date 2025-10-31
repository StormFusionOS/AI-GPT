"""Celery application entrypoint for CLI usage."""
from __future__ import annotations

from ops_api.orchestrator.celery_app import celery_app

__all__ = ["celery_app"]
