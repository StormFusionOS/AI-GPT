"""Compact Celery stub leveraged only in tests."""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional


class Ignore(Exception):
    """Exception signalling a task should be ignored."""


class Retry(Exception):
    """Exception mirroring Celery's retry semantics."""

    def __init__(self, exc: Exception | None = None, countdown: int = 0, kwargs: Optional[Dict[str, Any]] = None):
        super().__init__(exc)
        self.exc = exc
        self.countdown = countdown
        self.kwargs = kwargs or {}


class _Config:
    def __init__(self) -> None:
        self.task_always_eager = False
        self.task_eager_propagates = True
        self._values: Dict[str, Any] = {}

    def update(self, **kwargs: Any) -> None:
        self._values.update(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)


class Task:
    """Very small subset of Celery's Task base class."""

    abstract = False
    max_retries = 3

    def __init__(self) -> None:
        self.request = SimpleNamespace(retries=0)

    def before_start(self, task_id: str, args: tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
        return None

    def after_return(
        self,
        status: str,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any],
        exc: BaseException | None,
    ) -> None:
        return None

    def retry(self, exc: Exception | None = None, countdown: int = 0, kwargs: Optional[Dict[str, Any]] = None) -> None:
        raise Retry(exc=exc, countdown=countdown, kwargs=kwargs or {})


@dataclass
class _RegisteredTask:
    name: str
    base: type[Task]
    func: Callable[..., Any]
    max_retries: int

    def invoke(self, *args: Any, _task: Task | None = None, **kwargs: Any) -> Any:
        task = _task or self.base()
        task.name = self.name
        task.max_retries = self.max_retries
        task_id = getattr(task.request, "id", str(uuid.uuid4()))
        task.request.id = task_id
        try:
            task.before_start(task_id, args, kwargs)
            result = self.func(task, *args, **kwargs)
        except Retry as retry_exc:
            return self._handle_retry(task, task_id, args, kwargs, retry_exc)
        except Ignore:
            task.after_return("IGNORED", None, task_id, args, kwargs, None)
            return None
        except Exception as exc:  # pragma: no cover - defensive fallback
            task.after_return("FAILURE", None, task_id, args, kwargs, exc)
            return None
        else:
            task.after_return("SUCCESS", result, task_id, args, kwargs, None)
            return result

    def _handle_retry(
        self,
        task: Task,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any],
        retry_exc: Retry,
    ) -> Any:
        task.request.retries += 1
        if task.request.retries > task.max_retries:
            task.after_return("FAILURE", None, task_id, args, kwargs, retry_exc.exc)
            return None
        task.after_return("RETRY", None, task_id, args, kwargs, retry_exc.exc)
        merged_kwargs = dict(kwargs)
        merged_kwargs.update(retry_exc.kwargs)
        return self.invoke(*args, _task=task, **merged_kwargs)


class Celery:
    """Simple registry of tasks executed synchronously in tests."""

    def __init__(self, name: str, broker: str | None = None, backend: str | None = None, include: list[str] | None = None) -> None:
        self.name = name
        self.broker = broker
        self.backend = backend
        self.include = include or []
        self.conf = _Config()
        self._tasks: Dict[str, _RegisteredTask] = {}

    def task(
        self,
        name: str,
        *,
        bind: bool = False,
        base: type[Task] = Task,
        max_retries: int = 3,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            registered = _RegisteredTask(name=name, base=base if bind else Task, func=func, max_retries=max_retries)
            self._tasks[name] = registered

            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if bind:
                    return registered.invoke(*args, _task=base(), **kwargs)
                return registered.invoke(*args, **kwargs)

            return wrapper

        return decorator

    def send_task(self, name: str, kwargs: Optional[Dict[str, Any]] = None) -> Any:
        if name not in self._tasks:
            raise ValueError(f"Unknown task {name}")
        task_kwargs = kwargs or {}
        return self._tasks[name].invoke(**task_kwargs)


class _Logger:
    def info(self, *_: Any, **__: Any) -> None:  # pragma: no cover - noop
        return None

    def warning(self, *_: Any, **__: Any) -> None:  # pragma: no cover - noop
        return None

    def error(self, *_: Any, **__: Any) -> None:  # pragma: no cover - noop
        return None


def get_task_logger(*_: Any, **__: Any) -> _Logger:  # pragma: no cover - noop
    return _Logger()


@dataclass
class crontab:
    minute: str | int = "*"
    hour: str | int = "*"
    day_of_week: str | int = "*"
    day_of_month: str | int = "*"
    month_of_year: str | int = "*"


module = sys.modules[__name__]
sys.modules.setdefault("celery.exceptions", module)
sys.modules.setdefault("celery.utils", module)
sys.modules.setdefault("celery.utils.log", module)
sys.modules.setdefault("celery.schedules", module)

__all__ = [
    "Celery",
    "Task",
    "Ignore",
    "Retry",
    "get_task_logger",
    "crontab",
]
