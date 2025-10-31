"""Service helpers powering the client-facing portal endpoints.

These helpers are currently backed by an in-memory catalogue so the portal can
run end-to-end without a full persistence layer. They should be replaced by
real database queries once the production repositories are available.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List
import uuid

from app.schemas.client_portal import (
    Appointment,
    DashboardSummary,
    Interaction,
    Invoice,
    Profile,
)

# ---------------------------------------------------------------------------
# Sample dataset used for local development and automated UI tests. The layout
# mirrors the eventual database structures making it easy to replace the source
# of truth later on.
# ---------------------------------------------------------------------------
_SAMPLE_DATA: Dict[str, Dict[str, Any]] = {
    'client-001': {
        'profile': {
            'id': 'client-001',
            'name': 'River City Clean Co.',
            'primary_contact': 'Jordan Blake',
            'email': 'jordan@rivercityclean.com',
            'phone': '+1-555-0100',
            'address_line1': '401 Market Street',
            'address_line2': 'Suite 800',
            'city': 'Sacramento',
            'state_region': 'CA',
            'postal_code': '94203',
            'country': 'USA',
            'preferred_channel': 'email',
        },
        'credentials': {
            'email': 'jordan@rivercityclean.com',
            'password': 'client-portal-demo',
        },
        'appointments': [
            {
                'id': 'appt-100',
                'title': 'Monthly SEO Strategy Review',
                'start': datetime.utcnow() + timedelta(days=2, hours=3),
                'end': datetime.utcnow() + timedelta(days=2, hours=4),
                'status': 'scheduled',
                'staff_member': 'Alex Morgan',
                'location': 'Video Conference',
                'notes': 'Review rankings and paid spend rollup.',
            },
            {
                'id': 'appt-101',
                'title': 'Onsite Content Shoot',
                'start': datetime.utcnow() - timedelta(days=5, hours=2),
                'end': datetime.utcnow() - timedelta(days=5, hours=1),
                'status': 'completed',
                'staff_member': 'Nina Patel',
                'location': 'Client HQ',
                'notes': 'Captured testimonials and facility photos.',
            },
        ],
        'interactions': [
            {
                'id': 'msg-300',
                'channel': 'email',
                'direction': 'outbound',
                'subject': 'Updated keyword focus for Q2',
                'body_preview': 'We recommend targeting "eco friendly cleaning services"... ',
                'occurred_at': datetime.utcnow() - timedelta(hours=6),
                'staff_member': 'Alex Morgan',
            },
            {
                'id': 'msg-301',
                'channel': 'sms',
                'direction': 'inbound',
                'subject': 'Client Reply',
                'body_preview': 'Thanks for the update—excited to see results!',
                'occurred_at': datetime.utcnow() - timedelta(days=1, hours=2),
                'staff_member': 'Jordan Blake',
            },
        ],
        'invoices': [
            {
                'id': 'inv-500',
                'amount': 2850.00,
                'currency': 'USD',
                'status': 'due',
                'issued_at': datetime.utcnow() - timedelta(days=3),
                'due_date': datetime.utcnow() + timedelta(days=27),
                'description': 'April 2025 full-service SEO retainer',
                'pdf_url': 'https://example.com/invoices/inv-500.pdf',
            },
            {
                'id': 'inv-501',
                'amount': 2750.00,
                'currency': 'USD',
                'status': 'paid',
                'issued_at': datetime.utcnow() - timedelta(days=34),
                'due_date': datetime.utcnow() - timedelta(days=4),
                'description': 'March 2025 full-service SEO retainer',
                'pdf_url': 'https://example.com/invoices/inv-501.pdf',
            },
        ],
        'service_status': 'Monthly optimization in progress; next report delivers Friday.',
        'last_message_id': 601,
    }
}


def _require_client_record(client_id: str) -> Dict[str, Any]:
    if client_id not in _SAMPLE_DATA:
        raise KeyError(f'Unknown client id {client_id!r}')
    return _SAMPLE_DATA[client_id]


def get_dashboard_summary(client_id: str) -> DashboardSummary:
    record = _require_client_record(client_id)
    appointments = [Appointment.from_orm_raw(item) for item in record['appointments']]
    interactions = [Interaction.from_orm_raw(item) for item in record['interactions']]

    upcoming = [appt for appt in appointments if appt.start >= datetime.utcnow()]
    upcoming.sort(key=lambda appt: appt.start)
    recent_messages = sorted(interactions, key=lambda itm: itm.occurred_at, reverse=True)[:5]

    return DashboardSummary(
        client_name=record['profile']['name'],
        primary_contact=record['profile']['primary_contact'],
        service_status=record['service_status'],
        upcoming_appointments=upcoming,
        recent_communications=recent_messages,
        open_invoices=[inv for inv in list_invoices(client_id) if inv.status != 'paid'],
    )


def list_appointments(client_id: str) -> List[Appointment]:
    record = _require_client_record(client_id)
    appointments = [Appointment.from_orm_raw(item) for item in record['appointments']]
    appointments.sort(key=lambda appt: appt.start, reverse=True)
    return appointments


def list_interactions(client_id: str) -> List[Interaction]:
    record = _require_client_record(client_id)
    interactions = [Interaction.from_orm_raw(item) for item in record['interactions']]
    interactions.sort(key=lambda itm: itm.occurred_at, reverse=True)
    return interactions


def list_invoices(client_id: str) -> List[Invoice]:
    record = _require_client_record(client_id)
    invoices = [Invoice.from_orm_raw(item) for item in record['invoices']]
    invoices.sort(key=lambda inv: inv.issued_at, reverse=True)
    return invoices


def get_profile(client_id: str) -> Profile:
    record = _require_client_record(client_id)
    return Profile.from_orm_raw(record['profile'])


def update_profile(client_id: str, **changes: Any) -> Profile:
    record = _require_client_record(client_id)
    record['profile'] = {**record['profile'], **changes}
    return get_profile(client_id)


def record_client_message(client_id: str, channel: str, content: str) -> str:
    record = _require_client_record(client_id)
    # Incremental id ensures UI can render optimistic updates without conflicts.
    record['last_message_id'] += 1
    message_id = f'msg-{record["last_message_id"]}'
    new_message = {
        'id': message_id,
        'channel': channel,
        'direction': 'inbound',
        'subject': 'Client Portal Message',
        'body_preview': content[:120],
        'occurred_at': datetime.utcnow(),
        'staff_member': record['profile']['primary_contact'],
    }
    record['interactions'].append(new_message)
    return message_id


def acknowledge_reschedule_request(appointment_id: str, client_id: str, requested_start: datetime, message: str) -> Dict[str, Any]:
    """Return a payload confirming receipt of a reschedule request."""

    _require_client_record(client_id)
    return {
        'appointment_id': appointment_id,
        'requested_start': requested_start,
        'message': message,
        'received_at': datetime.utcnow(),
        'status': 'received',
    }


def change_password(client_id: str, new_password: str) -> None:
    """Placeholder handler for password updates.

    Real implementations will route to the authentication provider. The function
    exists so the API retains a consistent contract during local development.
    """

    _require_client_record(client_id)
    # Nothing to persist—password rotation happens in the identity provider.
    return None


def iter_clients() -> Iterable[str]:
    """Expose known client identifiers (used by MSW fixtures)."""

    return _SAMPLE_DATA.keys()


def remove_last_interaction(client_id: str) -> None:
    """Utility used by tests to keep the demo dataset deterministic."""

    record = _require_client_record(client_id)
    if record['interactions']:
        record['interactions'].pop()


def seed_with_client(profile: Profile) -> None:
    """Allow tests to register additional clients into the sample store."""

    _SAMPLE_DATA.setdefault(
        profile.id,
        {
            'profile': profile.dict(),
            'appointments': [],
            'interactions': [],
            'invoices': [],
            'service_status': 'Onboarding in progress.',
            'last_message_id': 1000,
        },
    )


def generate_invoice(client_id: str, amount: float, description: str) -> Invoice:
    """Utility for demos/tests to attach a new invoice to a client."""

    record = _require_client_record(client_id)
    invoice = Invoice.from_orm_raw(
        {
            'id': f'inv-{uuid.uuid4().hex[:8]}',
            'amount': amount,
            'currency': 'USD',
            'status': 'due',
            'issued_at': datetime.utcnow(),
            'due_date': datetime.utcnow() + timedelta(days=30),
            'description': description,
            'pdf_url': 'https://example.com/invoices/latest.pdf',
        }
    )
    record['invoices'].append(invoice.dict())
    return invoice


def authenticate(email: str, password: str) -> tuple[str, Profile]:
    """Validate client credentials and return identity details."""

    for client_id, record in _SAMPLE_DATA.items():
        credentials = record.get('credentials', {})
        if credentials.get('email', '').lower() == email.lower() and credentials.get('password') == password:
            return client_id, get_profile(client_id)
    raise ValueError('Invalid credentials')


def issue_token(client_id: str) -> str:
    """Generate a deterministic mock token for local development."""

    return f'mock-client-token-{client_id}'
