from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app.api.deps import require_sales_claims
from app.api.routes.leads import list_leads


def test_sales_role_allowed(override_settings) -> None:
    claims = asyncio.run(require_sales_claims({"role": "SALES"}))
    response = list_leads(claims=claims)
    assert isinstance(response, list)


def test_ops_role_rejected(override_settings) -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(require_sales_claims({"role": "SEO_ENGINEER"}))
    assert exc.value.status_code == 403

