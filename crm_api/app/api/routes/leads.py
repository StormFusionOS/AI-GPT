"""Lead and contact endpoints."""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ...core.security import decode_token, role_guard
from ...db import (
    count_leads,
    count_won_leads,
    create_contact_record,
    delete_contact_record,
    list_contact_records,
)
from ...models import LeadStatus, UserRole
from ...schemas.contact import ContactCreate, ContactRead, DashboardSummary

router = APIRouter(prefix="/leads", tags=["leads"])

_ALLOWED = {UserRole.SALES.value, UserRole.SALES_MANAGER.value, UserRole.OWNER.value}


def _assert_role(authorization: str) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    claims = decode_token(authorization.split(" ", 1)[1])
    role_guard(_ALLOWED)(claims)
    return claims


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(authorization: str) -> DashboardSummary:
    _assert_role(authorization)
    total = count_leads()
    won = count_won_leads()
    return DashboardSummary(total_leads=total, won_leads=won, upcoming_appointments=0)


@router.post("/contacts", response_model=ContactRead)
def create_contact(payload: ContactCreate, authorization: str) -> ContactRead:
    _assert_role(authorization)
    contact = create_contact_record(payload.name, payload.email, payload.phone)
    return ContactRead(id=contact.id, name=contact.name, email=contact.email, phone=contact.phone)


@router.get("/contacts", response_model=List[ContactRead])
def list_contacts(authorization: str) -> List[ContactRead]:
    _assert_role(authorization)
    return [ContactRead(id=item.id, name=item.name, email=item.email, phone=item.phone) for item in list_contact_records()]


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: UUID, authorization: str) -> None:
    _assert_role(authorization)
    contacts = list_contact_records()
    target = next((c for c in contacts if c.id == contact_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    delete_contact_record(contact_id)
