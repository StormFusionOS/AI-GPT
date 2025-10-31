"""SQLAlchemy models backing the CRM schema for migrations and drift checks."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, MetaData, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class CRMBase(DeclarativeBase):
    """Declarative base targeting the ``crm`` schema."""

    metadata = MetaData(schema="crm")


class UserRoleEnum(str):
    """String mixin for Enum naming helper."""


USER_ROLE = Enum(
    "SALES",
    "SALES_MANAGER",
    "OWNER",
    "CLIENT",
    name="user_role",
)

LEAD_STATUS = Enum(
    "NEW",
    "CONTACTED",
    "QUALIFIED",
    "WON",
    "LOST",
    name="lead_status",
)

INTERACTION_TYPE = Enum(
    "SMS_IN",
    "SMS_OUT",
    "EMAIL_IN",
    "EMAIL_OUT",
    "CALL_IN",
    "CALL_OUT",
    "FB_MSG",
    "IG_DM",
    name="interaction_type",
)

AUTO_REPLY_CHANNEL = Enum("SMS", "EMAIL", name="auto_reply_channel")


class User(CRMBase):
    """Application user definition."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(String(36), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(USER_ROLE, nullable=False, default="SALES")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    leads: Mapped[list["Lead"]] = relationship(back_populates="owner", cascade="all,delete")


class Contact(CRMBase):
    """CRM contact record."""

    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(String(36), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID | None] = mapped_column(String(36), ForeignKey("crm.users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    leads: Mapped[list["Lead"]] = relationship(back_populates="contact", cascade="all,delete")


class Lead(CRMBase):
    """Sales pipeline lead information."""

    __tablename__ = "leads"

    id: Mapped[UUID] = mapped_column(String(36), primary_key=True, default=uuid4)
    contact_id: Mapped[UUID] = mapped_column(String(36), ForeignKey("crm.contacts.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[UUID | None] = mapped_column(String(36), ForeignKey("crm.users.id"), nullable=True)
    status: Mapped[str] = mapped_column(LEAD_STATUS, nullable=False, default="NEW")
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_value: Mapped[Optional[Numeric]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    contact: Mapped[Contact] = relationship(back_populates="leads")
    owner: Mapped[Optional[User]] = relationship(back_populates="leads")


class Interaction(CRMBase):
    """Recorded inbound/outbound communications."""

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lead_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("crm.leads.id", ondelete="SET NULL"), nullable=True
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crm.contacts.id", ondelete="CASCADE"), nullable=False
    )
    interaction_type: Mapped[str] = mapped_column(INTERACTION_TYPE, nullable=False)
    channel_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    contact: Mapped[Contact] = relationship()
    lead: Mapped[Optional[Lead]] = relationship()


class AutoReplyRule(CRMBase):
    """Configurable auto-reply template per channel."""

    __tablename__ = "auto_reply_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    channel: Mapped[str] = mapped_column(AUTO_REPLY_CHANNEL, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    after_hours_template: Mapped[str] = mapped_column(Text, nullable=False)
    business_hours_start: Mapped[int] = mapped_column(nullable=False, default=8)
    business_hours_end: Mapped[int] = mapped_column(nullable=False, default=18)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)


__all__ = [
    "CRMBase",
    "User",
    "Contact",
    "Lead",
    "Interaction",
    "AutoReplyRule",
]
