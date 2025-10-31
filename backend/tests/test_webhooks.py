"""Webhook ingestion tests to ensure integrations can be validated."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.services import client_portal


def test_twilio_sms_webhook_records_interaction(client: TestClient) -> None:
    before = len(client_portal.list_interactions('client-001'))

    response = client.post(
        '/api/webhooks/twilio/sms',
        data={
            'From': '+15550123',
            'To': '+15559876',
            'Body': 'Hello from Twilio!',
            'MessageSid': 'SM123',
            'AccountSid': 'AC999',
        },
        headers={'X-Twilio-Signature': 'test-signature'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'accepted'

    after = len(client_portal.list_interactions('client-001'))
    assert after == before + 1

    # Clean up the appended interaction so other tests remain deterministic.
    client_portal.remove_last_interaction('client-001')
