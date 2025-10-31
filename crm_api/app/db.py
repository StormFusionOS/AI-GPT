"""Lightweight data access helpers backed by an in-memory store."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, Optional
from uuid import UUID, uuid4

from .models import (
    AutoReplyChannel,
    AutoReplyRule,
    Contact,
    DB,
    Interaction,
    InteractionType,
    Lead,
    LeadStatus,
)


@contextmanager
def session_scope() -> Iterator[None]:
    """Compatibility shim matching SQLAlchemy's session_scope pattern."""

    yield


def init_db() -> None:  # pragma: no cover - nothing to initialise for in-memory store
    DB.reset()


def _find_contact_by_email_or_phone(email: str | None, phone: str | None) -> Optional[Contact]:
    for contact in DB.contacts.values():
        if email and contact.email and contact.email.lower() == email.lower():
            return contact
        if phone and contact.phone and contact.phone == phone:
            return contact
    return None


def upsert_contact_record(name: str, email: str | None, phone: str | None) -> Contact:
    existing = _find_contact_by_email_or_phone(email, phone)
    if existing:
        if name and existing.name != name:
            existing.name = name
        if email and existing.email != email:
            existing.email = email
        if phone and existing.phone != phone:
            existing.phone = phone
        existing.updated_at = datetime.utcnow()
        return existing

    contact = Contact(id=uuid4(), name=name or "Prospect", email=email, phone=phone)
    DB.contacts[contact.id] = contact
    return contact


def list_contact_records() -> list[Contact]:
    return list(DB.contacts.values())


def delete_contact_record(contact_id: UUID) -> None:
    DB.contacts.pop(contact_id, None)


def _find_lead(contact_id: UUID, source: str | None) -> Optional[Lead]:
    for lead in DB.leads.values():
        if lead.contact_id == contact_id and lead.source == source:
            return lead
    return None


def ensure_lead(contact_id: UUID, source: str | None) -> Lead:
    lead = _find_lead(contact_id, source)
    if lead:
        return lead
    lead = Lead(id=uuid4(), contact_id=contact_id, source=source)
    DB.leads[lead.id] = lead
    return lead


def count_leads() -> int:
    return len(DB.leads)


def count_won_leads() -> int:
    return sum(1 for lead in DB.leads.values() if lead.status == LeadStatus.WON)


def list_lead_records() -> list[Lead]:
    return list(DB.leads.values())


def get_lead(lead_id: UUID) -> Optional[Lead]:
    return DB.leads.get(lead_id)


def record_interaction(
    lead_id: UUID | None,
    contact_id: UUID,
    interaction_type: InteractionType,
    content: str,
    channel_id: str | None = None,
) -> Interaction:
    interaction = Interaction(
        id=uuid4(),
        lead_id=lead_id,
        contact_id=contact_id,
        interaction_type=interaction_type,
        channel_id=channel_id,
        content=content,
    )
    DB.interactions[interaction.id] = interaction
    return interaction


def list_interactions_for_lead(lead_id: UUID) -> list[Interaction]:
    return sorted(
        (i for i in DB.interactions.values() if i.lead_id == lead_id),
        key=lambda item: item.occurred_at,
    )


def list_interactions_for_contact(contact_id: UUID) -> list[Interaction]:
    return sorted(
        (i for i in DB.interactions.values() if i.contact_id == contact_id),
        key=lambda item: item.occurred_at,
    )


def get_auto_reply_rule(channel: AutoReplyChannel) -> AutoReplyRule | None:
    return DB.auto_reply_rules.get(channel)


def upsert_auto_reply_rule(rule: AutoReplyRule) -> AutoReplyRule:
    DB.auto_reply_rules[rule.channel] = rule
    return rule
