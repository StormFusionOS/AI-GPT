"""Lead and contact endpoints."""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ...core.security import decode_token, role_guard
from ...db import (
    count_leads,
    count_won_leads,
    delete_contact_record,
    list_contact_records,
    list_interactions_for_lead,
    list_lead_records,
    upsert_contact_record,
)
from ...models import UserRole
from ...schemas.contact import (
    ContactCreate,
    ContactRead,
    DashboardSummary,
    InteractionRead,
    LeadBoardItem,
)

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
    contact = upsert_contact_record(payload.name, payload.email, payload.phone)
    return ContactRead(id=contact.id, name=contact.name, email=contact.email, phone=contact.phone)


@router.get("/contacts", response_model=List[ContactRead])
def list_contacts(authorization: str) -> List[ContactRead]:
    _assert_role(authorization)
    return [ContactRead(id=item.id, name=item.name, email=item.email, phone=item.phone) for item in list_contact_records()]


@router.get("", response_model=List[LeadBoardItem])
def list_leads(authorization: str) -> List[LeadBoardItem]:
    _assert_role(authorization)
    board: List[LeadBoardItem] = []
    contacts = {contact.id: contact for contact in list_contact_records()}
    for lead in list_lead_records():
        contact = contacts.get(lead.contact_id)
        last_message = None
        interactions = list_interactions_for_lead(lead.id)
        if interactions:
            last_message = interactions[-1].content
        board.append(
            LeadBoardItem(
                id=lead.id,
                contact_id=lead.contact_id,
                contact_name=contact.name if contact else "Unknown",
                status=lead.status,
                source=lead.source,
                created_at=lead.created_at,
                last_message_preview=last_message,
            )
        )
    return board


@router.get("/{lead_id}/interactions", response_model=List[InteractionRead])
def lead_interactions(lead_id: UUID, authorization: str) -> List[InteractionRead]:
    _assert_role(authorization)
    items = list_interactions_for_lead(lead_id)
    return [
        InteractionRead(
            id=interaction.id,
            lead_id=interaction.lead_id,
            contact_id=interaction.contact_id,
            interaction_type=interaction.interaction_type,
            content=interaction.content,
            occurred_at=interaction.occurred_at,
        )
        for interaction in items
    ]


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: UUID, authorization: str) -> None:
    _assert_role(authorization)
    contacts = list_contact_records()
    target = next((c for c in contacts if c.id == contact_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    delete_contact_record(contact_id)
