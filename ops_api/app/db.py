"""Database utilities for ops API."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .core.config import get_settings

OPS_SCHEMA = "ops"

Base = declarative_base()


def _create_engine() -> Engine:
    settings = get_settings()
    connect_args: dict[str, object] = {}
    url = settings.database_url
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
    if url.startswith("sqlite"):
        engine = engine.execution_options(schema_translate_map={OPS_SCHEMA: None})
    return engine


def _get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


engine = _create_engine()
SessionLocal = _get_session_factory(engine)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def reset_engine() -> None:
    global engine
    new_engine = _create_engine()
    engine = new_engine
    SessionLocal.configure(bind=engine)
