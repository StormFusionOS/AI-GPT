"""Security helpers for ops API."""
from __future__ import annotations

import base64
import base64
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable

from fastapi import HTTPException, status

from .core.config import get_settings


class RoleGuard:
    def __init__(self, allowed_roles: Iterable[str]):
        self.allowed_roles = set(allowed_roles)

    def __call__(self, claims: Dict[str, Any]) -> None:
        role = claims.get("role")
        if role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


def _sign(payload: Dict[str, Any]) -> str:
    settings = get_settings()
    message = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(settings.secret_key.encode("utf-8"), message, "sha256").digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def create_token(payload: Dict[str, Any], *, expires_delta: timedelta) -> str:
    data = payload.copy()
    data["exp"] = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    token_bytes = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = _sign(data)
    return base64.urlsafe_b64encode(token_bytes).decode("utf-8").rstrip("=") + "." + signature


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload_b64, signature = token.split(".")
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        data: Dict[str, Any] = json.loads(payload_json)
        if _sign(data) != signature:
            raise ValueError("Bad signature")
        exp = data.get("exp")
        if exp is not None and datetime.now(timezone.utc).timestamp() > exp:
            raise ValueError("Expired")
        return data
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
