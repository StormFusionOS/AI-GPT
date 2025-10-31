"""Pydantic schemas for the contacts CRUD API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    name: str = Field(..., description='Full name of the contact')
    email: Optional[EmailStr] = Field(default=None, description='Primary email address')
    phone: Optional[str] = Field(default=None, description='Primary phone number')
    company: Optional[str] = Field(default=None, description='Associated company or organization')
    notes: Optional[str] = Field(default=None, description='Internal notes about the contact')


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ContactRead(ContactBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime = Field(alias='updatedAt')

    class Config:
        from_attributes = True
        populate_by_name = True
