"""Token helper tests for CRM API."""
from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import create_token, decode_token


@pytest.mark.usefixtures("override_settings")
def test_create_and_decode_token_success() -> None:
    settings = get_settings()
    token = create_token(
        {"sub": "user-123", "role": "SALES"},
        expires_delta=timedelta(minutes=5),
        secret=settings.secret_key,
    )

    claims = decode_token(token, secret=settings.secret_key)
    assert claims["sub"] == "user-123"
    assert claims["role"] == "SALES"
    assert claims["exp"] > claims["iat"] >= claims["nbf"]


@pytest.mark.usefixtures("override_settings")
def test_decode_token_expired() -> None:
    settings = get_settings()
    token = create_token(
        {"sub": "user-123"},
        expires_delta=timedelta(seconds=-1),
        secret=settings.secret_key,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, secret=settings.secret_key)


@pytest.mark.usefixtures("override_settings")
def test_decode_token_bad_signature() -> None:
    settings = get_settings()
    token = create_token(
        {"sub": "user-123"},
        expires_delta=timedelta(minutes=5),
        secret=settings.secret_key,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(token, secret="wrong-secret")
