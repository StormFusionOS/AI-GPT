"""Webhook ingestion tests."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from uuid import UUID, uuid4

from app.api.routes.auth import login
from app.core.config import get_settings
from app.db import init_db, list_interactions_for_lead, list_lead_records, DB
from app.models import InteractionType, User, UserRole
from app.schemas.auth import LoginRequest
from app.services.email_poller import EmailPoller


def _auth_header() -> dict[str, str]:
    token_pair = login(LoginRequest(email="sales@example.com", password="password123"))
    return {"Authorization": f"Bearer {token_pair.access_token}"}


def test_facebook_webhook_creates_lead_and_autoreply(client) -> None:
    settings = get_settings()
    payload = {
        "entry": [
            {
                "id": "123",
                "field_data": [
                    {"name": "full_name", "values": ["Jane Prospect"]},
                    {"name": "email", "values": ["jane@example.com"]},
                    {"name": "phone_number", "values": ["+15555550123"]},
                    {"name": "message", "values": ["Interested in services"]},
                ],
            }
        ]
    }
    response = client.post(
        "/api/v1/webhooks/facebook/lead",
        json=payload,
        headers={"X-Hub-Signature": settings.facebook_verify_token},
    )
    assert response.status_code == 200
    lead_id = UUID(response.json()["lead_id"])
    interactions = list_interactions_for_lead(lead_id)
    assert interactions[0].interaction_type == InteractionType.FB_MSG
    assert any(item.interaction_type in {InteractionType.SMS_OUT, InteractionType.EMAIL_OUT} for item in interactions)

    leads_response = client.get("/api/v1/leads", headers=_auth_header())
    assert leads_response.status_code == 200
    lead_ids = {UUID(item["id"]) for item in leads_response.json()}
    assert lead_id in lead_ids


def test_twilio_webhook_valid_signature(client) -> None:
    settings = get_settings()
    payload = {"From": "+15551234567", "To": "+18005551234", "Body": "Need a quote", "MessageSid": "SM123"}
    body = json.dumps(payload).encode("utf-8")
    signature = base64.b64encode(hmac.new(settings.twilio_auth_token.encode("utf-8"), body, hashlib.sha256).digest()).decode("utf-8")

    response = client.post(
        "/api/v1/webhooks/twilio/sms",
        data=body,
        headers={"Content-Type": "application/json", "X-Twilio-Signature": signature},
    )
    assert response.status_code == 200
    lead_id = UUID(response.json()["lead_id"])
    interactions = list_interactions_for_lead(lead_id)
    assert interactions[0].interaction_type == InteractionType.SMS_IN
    assert any(item.interaction_type == InteractionType.SMS_OUT for item in interactions[1:])


def test_email_poller_ingests_message() -> None:
    init_db()
    import hashlib

    hashed = hashlib.sha256("password123".encode("utf-8")).hexdigest()
    DB.users["sales@example.com"] = User(id=uuid4(), email="sales@example.com", hashed_password=hashed, role=UserRole.SALES)
    poller = EmailPoller(interval_seconds=0)
    poller.enqueue(
        subject="Thumbtack lead",
        body="Name: John Sample\nEmail: john@example.com\nPhone: +15550001111\nMessage: Need cleaning",
        source="thumbtack",
    )
    # Run one iteration synchronously
    import asyncio

    asyncio.run(poller.poll_once())
    # The poller should produce a lead and auto reply (SMS because of phone)
    # Find the most recent lead and inspect interactions
    leads = list_lead_records()
    assert leads, "expected at least one lead from email poller"
    lead_id = leads[-1].id
    interactions = list_interactions_for_lead(lead_id)
    assert interactions[0].interaction_type == InteractionType.EMAIL_IN
    assert any(item.interaction_type in {InteractionType.SMS_OUT, InteractionType.EMAIL_OUT} for item in interactions[1:])
