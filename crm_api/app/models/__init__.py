"""In-memory data models for the CRM service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4


class UserRole(str, Enum):
    SALES = "SALES"
    SALES_MANAGER = "SALES_MANAGER"
    OWNER = "OWNER"
    CLIENT = "CLIENT"


@dataclass
class User:
    id: UUID
    email: str
    hashed_password: str
    role: UserRole
    created_at: datetime = field(default_factory=datetime.utcnow)


class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    WON = "WON"
    LOST = "LOST"


@dataclass
class Contact:
    id: UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Lead:
    id: UUID
    contact_id: UUID
    status: LeadStatus = LeadStatus.NEW
    source: Optional[str] = None
    estimated_value: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class Database:
    """Simple in-memory database used for unit tests."""

    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self.contacts: Dict[UUID, Contact] = {}
        self.leads: Dict[UUID, Lead] = {}

    def reset(self) -> None:
        self.users.clear()
        self.contacts.clear()
        self.leads.clear()


DB = Database()
