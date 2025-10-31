"""Simple data models for the ops service."""
from __future__ import annotations

from .service_health import ServiceHealth
from .task_runs import TaskRun

__all__ = ["ServiceHealth", "TaskRun"]
