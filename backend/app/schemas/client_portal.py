"""Pydantic models representing client portal payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, TypeVar, Type

from pydantic import BaseModel, Field


TOrmModel = TypeVar('TOrmModel', bound='_OrmFriendlyModel')


class _OrmFriendlyModel(BaseModel):
    """Base model that offers a helper to hydrate from ORM-like dicts."""

    @classmethod
    def from_orm_raw(cls: Type[TOrmModel], payload: dict) -> TOrmModel:
        return cls(**payload)

    class Config:
        orm_mode = True


class Appointment(_OrmFriendlyModel):
    id: str
    title: str
    start: datetime
    end: datetime
    status: str
    staff_member: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class Interaction(_OrmFriendlyModel):
    id: str
    channel: str
    direction: str
    subject: str
    body_preview: str
    occurred_at: datetime
    staff_member: Optional[str] = None


class Invoice(_OrmFriendlyModel):
    id: str
    amount: float
    currency: str = Field(default='USD', max_length=3)
    status: str
    issued_at: datetime
    due_date: datetime
    description: Optional[str] = None
    pdf_url: Optional[str] = None


class Profile(_OrmFriendlyModel):
    id: str
    name: str
    primary_contact: str
    email: str
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    preferred_channel: Optional[str] = None


class DashboardSummary(BaseModel):
    client_name: str
    primary_contact: str
    service_status: str
    upcoming_appointments: list[Appointment]
    recent_communications: list[Interaction]
    open_invoices: list[Invoice]


class MessageRequest(BaseModel):
    channel: str = Field(pattern='^(email|sms|portal)$')
    content: str = Field(min_length=1, max_length=4000)


class RescheduleRequest(BaseModel):
    requested_start: datetime
    message: str = Field(min_length=1, max_length=2000)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    primary_contact: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    preferred_channel: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    client_id: str
    name: str
    primary_contact: str
