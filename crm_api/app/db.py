"""Lightweight data access helpers backed by an in-memory store."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from uuid import UUID, uuid4

from .models import Contact, DB, Lead


@contextmanager
def session_scope() -> Iterator[None]:
    """Compatibility shim matching SQLAlchemy's session_scope pattern."""

    yield


def init_db() -> None:  # pragma: no cover - nothing to initialise for in-memory store
    DB.reset()


def create_contact_record(name: str, email: str | None, phone: str | None) -> Contact:
    contact = Contact(id=uuid4(), name=name, email=email, phone=phone)
    DB.contacts[contact.id] = contact
    return contact


def list_contact_records() -> list[Contact]:
    return list(DB.contacts.values())


def delete_contact_record(contact_id: UUID) -> None:
    DB.contacts.pop(contact_id, None)


def count_leads() -> int:
    return len(DB.leads)


def count_won_leads() -> int:
    return sum(1 for lead in DB.leads.values() if lead.status.name == "WON")
