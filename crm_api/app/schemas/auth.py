"""Authentication schemas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


@dataclass
class LoginRequest:
    email: str
    password: str


@dataclass
class TokenPayload:
    sub: str
    role: str
    client_id: UUID | None = None
    exp: int | None = None
