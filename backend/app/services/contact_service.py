"""Database-backed CRUD helpers for the contacts API."""
from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Contact
from app.schemas import ContactCreate, ContactRead, ContactUpdate


class ContactService:
    """Encapsulates contact persistence logic for reuse in routes and tests."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_contacts(self) -> list[ContactRead]:
        results: Iterable[Contact] = self.session.scalars(select(Contact).order_by(Contact.created_at.desc()))
        return [ContactRead.model_validate(row, from_attributes=True) for row in results]

    def create_contact(self, payload: ContactCreate) -> ContactRead:
        contact = Contact(**payload.model_dump(exclude_none=True))
        self.session.add(contact)
        self._commit()
        return ContactRead.model_validate(contact, from_attributes=True)

    def get_contact(self, contact_id: str) -> ContactRead:
        contact = self.session.get(Contact, contact_id)
        if contact is None:
            raise KeyError(contact_id)
        return ContactRead.model_validate(contact, from_attributes=True)

    def update_contact(self, contact_id: str, payload: ContactUpdate) -> ContactRead:
        contact = self.session.get(Contact, contact_id)
        if contact is None:
            raise KeyError(contact_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(contact, field, value)
        self._commit()
        self.session.refresh(contact)
        return ContactRead.model_validate(contact, from_attributes=True)

    def delete_contact(self, contact_id: str) -> None:
        contact = self.session.get(Contact, contact_id)
        if contact is None:
            raise KeyError(contact_id)
        self.session.delete(contact)
        self._commit()

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError('Contact constraint violated') from exc


__all__ = ['ContactService']
