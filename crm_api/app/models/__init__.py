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


class InteractionType(str, Enum):
    SMS_IN = "SMS_IN"
    SMS_OUT = "SMS_OUT"
    EMAIL_IN = "EMAIL_IN"
    EMAIL_OUT = "EMAIL_OUT"
    CALL_IN = "CALL_IN"
    CALL_OUT = "CALL_OUT"
    FB_MSG = "FB_MSG"
    IG_DM = "IG_DM"


@dataclass
class Interaction:
    id: UUID
    lead_id: Optional[UUID]
    contact_id: UUID
    interaction_type: InteractionType
    channel_id: Optional[str]
    content: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)


class AutoReplyChannel(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"


@dataclass
class AutoReplyRule:
    id: UUID
    channel: AutoReplyChannel
    template: str
    after_hours_template: str
    business_hours_start: int
    business_hours_end: int
    enabled: bool = True


class Database:
    """Simple in-memory database used for unit tests."""

    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self.contacts: Dict[UUID, Contact] = {}
        self.leads: Dict[UUID, Lead] = {}
        self.interactions: Dict[UUID, Interaction] = {}
        self.auto_reply_rules: Dict[AutoReplyChannel, AutoReplyRule] = {}

    def _seed_rules(self) -> None:
        """Populate default auto-reply rules for tests and local development."""

        if AutoReplyChannel.SMS not in self.auto_reply_rules:
            self.auto_reply_rules[AutoReplyChannel.SMS] = AutoReplyRule(
                id=uuid4(),
                channel=AutoReplyChannel.SMS,
                template="Hi {name}, thanks for reaching out! A team member will reply shortly.",
                after_hours_template="Hi {name}, thanks for reaching out! Our team will contact you next business day.",
                business_hours_start=8,
                business_hours_end=18,
            )
        if AutoReplyChannel.EMAIL not in self.auto_reply_rules:
            self.auto_reply_rules[AutoReplyChannel.EMAIL] = AutoReplyRule(
                id=uuid4(),
                channel=AutoReplyChannel.EMAIL,
                template="Hello {name}, thanks for contacting us. We'll follow up soon.",
                after_hours_template="Hello {name}, our office is currently closed. We'll get back to you ASAP.",
                business_hours_start=8,
                business_hours_end=18,
            )

    def reset(self) -> None:
        self.users.clear()
        self.contacts.clear()
        self.leads.clear()
        self.interactions.clear()
        self.auto_reply_rules.clear()
        self._seed_rules()


DB = Database()

__all__ = [
    "User",
    "UserRole",
    "LeadStatus",
    "Contact",
    "Lead",
    "Interaction",
    "InteractionType",
    "AutoReplyChannel",
    "AutoReplyRule",
    "Database",
    "DB",
]
