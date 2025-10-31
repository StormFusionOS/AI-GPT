"""Contacts endpoint tests."""
from __future__ import annotations

from uuid import UUID

from app.api.routes.auth import login
from app.api.routes.leads import create_contact, delete_contact, list_contacts
from app.schemas.auth import LoginRequest
from app.schemas.contact import ContactCreate


def _token() -> str:
    token_pair = login(LoginRequest(email="sales@example.com", password="password123"))
    return token_pair.access_token


def test_create_and_list_contact(override_settings) -> None:
    token = _token()
    contact = create_contact(ContactCreate(name="Jane", email="jane@example.com"), authorization=f"Bearer {token}")
    assert contact.email == "jane@example.com"
    contacts = list_contacts(authorization=f"Bearer {token}")
    assert any(item.email == "jane@example.com" for item in contacts)


def test_delete_contact(override_settings) -> None:
    token = _token()
    created = create_contact(ContactCreate(name="Mark"), authorization=f"Bearer {token}")
    delete_contact(UUID(str(created.id)), authorization=f"Bearer {token}")
    contacts = list_contacts(authorization=f"Bearer {token}")
    assert all(item.id != created.id for item in contacts)
