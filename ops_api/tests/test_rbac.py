from __future__ import annotations

import asyncio

import pytest

from app.api.deps import require_ops_claims
from app.api.routes.orchestrator import get_health
from app.db import DatabaseSession


def test_ops_role_can_access(db_session: DatabaseSession) -> None:
    claims = asyncio.run(require_ops_claims({"role": "DEVOPS"}))
    response = get_health(claims=claims, session=db_session)
    assert response.services == []


def test_crm_role_forbidden() -> None:
    try:
        asyncio.run(require_ops_claims({"role": "SALES"}))
    except Exception as exc:  # pragma: no cover - exercised in tests
        assert getattr(exc, "status_code", None) == 403
    else:  # pragma: no cover - guard
        pytest.fail("CRM role unexpectedly permitted")

