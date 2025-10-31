"""Test fixtures shared across backend pytest suites."""
from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session
from app.main import app
from app.models import Base, Contact  # noqa: F401 - ensure model registration

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'sqlite+pysqlite:///./test_suite.db')


@pytest.fixture(scope='session')
def engine() -> Generator:
    """Initialise an isolated database engine for integration tests."""

    connect_args = {'check_same_thread': False} if TEST_DATABASE_URL.startswith('sqlite') else {}
    engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope='function')
def db_session(engine) -> Generator[Session, None, None]:
    """Provide a database session wrapped in a transaction per test."""

    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with the database dependency overridden."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture(scope='function')
def client_headers() -> dict[str, str]:
    """Headers representing an authenticated demo client."""

    return {'X-User-Role': 'client', 'X-Client-Id': 'client-001'}
