"""Contact and lead schemas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ..models import InteractionType, LeadStatus


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
class LeadBoardItem:
    id: UUID
    contact_id: UUID
    contact_name: str
    status: LeadStatus
    source: str | None
    created_at: datetime
    last_message_preview: str | None


@dataclass
class InteractionRead:
    id: UUID
    lead_id: UUID | None
    contact_id: UUID
    interaction_type: InteractionType
    content: str
    occurred_at: datetime


@dataclass
class DashboardSummary:
    total_leads: int
    won_leads: int
    upcoming_appointments: int
