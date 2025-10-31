"""Contact and lead schemas."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from ..models import LeadStatus


@dataclass
class ContactCreate:
    name: str
    email: str | None = None
    phone: str | None = None


@dataclass
class ContactRead:
    id: UUID
    name: str
    email: str | None
    phone: str | None


@dataclass
class LeadRead:
    id: UUID
    contact_id: UUID
    status: LeadStatus
    source: str | None
    estimated_value: Decimal | None


@dataclass
class DashboardSummary:
    total_leads: int
    won_leads: int
    upcoming_appointments: int
