"""Webhook endpoints for third-party integrations used in tests."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Form, Header, HTTPException, status

from app.services import client_portal

router = APIRouter(prefix='/webhooks', tags=['webhooks'])


@router.post('/twilio/sms', status_code=status.HTTP_200_OK)
async def ingest_twilio_sms(
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    x_twilio_signature: str | None = Header(default=None, alias='X-Twilio-Signature'),
) -> dict[str, str]:
    """Store inbound SMS as a client interaction.

    Signature validation is deferred for the scaffold—tests may override the
    dependency to skip verification while still asserting behaviour.
    """

    if not x_twilio_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Missing signature header')

    # Preserve unused form parameters for future enrichment while appeasing linters.
    _ = (From, To, AccountSid)

    client_portal.record_client_message('client-001', channel='sms', content=Body)
    return {
        'status': 'accepted',
        'processedAt': datetime.utcnow().isoformat(),
        'messageSid': MessageSid,
    }
