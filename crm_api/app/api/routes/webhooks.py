"""Inbound webhook endpoints for lead ingestion."""
from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status
import structlog

from ...core.config import get_settings
from ...models import InteractionType
from ...schemas.webhooks import (
    FacebookLeadPayload,
    GoogleLeadPayload,
    TwilioSMSPayload,
    TwilioVoicePayload,
)
from ...services.intake import ingest_lead

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _compare_secret(provided: str | None, expected: str, error_detail: str) -> None:
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_detail)


def _extract_field_map(payload: FacebookLeadPayload) -> tuple[Dict[str, str], str | None]:
    for fb_entry in payload.entry:
        values = {field.name: (field.values[0] if field.values else "") for field in fb_entry.field_data}
        if values:
            return values, fb_entry.id
    return {}, None


@router.post("/facebook/lead")
async def facebook_lead(payload: FacebookLeadPayload, request: Request) -> dict[str, Any]:
    settings = get_settings()
    _compare_secret(
        request.headers.get("X-Hub-Signature"),
        settings.facebook_verify_token,
        "invalid facebook token",
    )
    data, entry_id = _extract_field_map(payload)
    if not data:
        raise HTTPException(status_code=400, detail="missing lead data")

    name = data.get("full_name") or data.get("name") or "Facebook Lead"
    email = data.get("email") or data.get("email_address")
    phone = data.get("phone_number") or data.get("phone")
    message = data.get("message") or data.get("comments") or "Facebook lead form submission"

    lead, contact = ingest_lead(
        name=name,
        email=email,
        phone=phone,
        message=message,
        source="facebook",
        inbound_type=InteractionType.FB_MSG,
        channel_id=entry_id,
    )
    logger.info("facebook-lead-ingested", contact_id=str(contact.id), lead_id=str(lead.id))
    return {"status": "accepted", "lead_id": str(lead.id)}


@router.post("/google-ads/lead")
async def google_ads_lead(payload: GoogleLeadPayload, request: Request) -> dict[str, Any]:
    settings = get_settings()
    _compare_secret(
        request.headers.get("X-Goog-Ads-Signature"),
        settings.google_leads_verify_key,
        "invalid google ads signature",
    )
    data = payload.lead_data or {}
    name = data.get("fullName") or data.get("name") or "Google Lead"
    email = data.get("email")
    phone = data.get("phoneNumber") or data.get("phone")
    message = data.get("notes") or data.get("message") or "Google Lead Form submission"

    lead, contact = ingest_lead(
        name=name,
        email=email,
        phone=phone,
        message=message,
        source="google_ads",
        inbound_type=InteractionType.EMAIL_IN,
        channel_id=payload.lead_id,
    )
    logger.info("google-lead-ingested", contact_id=str(contact.id), lead_id=str(lead.id))
    return {"status": "accepted", "lead_id": str(lead.id)}


def _twilio_signature(body: bytes, auth_token: str) -> str:
    digest = hmac.new(auth_token.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


@router.post("/twilio/sms")
async def twilio_sms(payload: TwilioSMSPayload, request: Request) -> dict[str, Any]:
    settings = get_settings()
    raw_body = await request.body()
    expected = _twilio_signature(raw_body, settings.twilio_auth_token)
    if not hmac.compare_digest(request.headers.get("X-Twilio-Signature", ""), expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid twilio signature")

    lead, contact = ingest_lead(
        name=payload.from_number,
        email=None,
        phone=payload.from_number,
        message=payload.body,
        source="twilio_sms",
        inbound_type=InteractionType.SMS_IN,
        channel_id=payload.message_sid,
    )
    logger.info("twilio-sms-ingested", contact_id=str(contact.id), lead_id=str(lead.id))
    return {"status": "accepted", "lead_id": str(lead.id)}


@router.post("/twilio/voice")
async def twilio_voice(payload: TwilioVoicePayload, request: Request) -> dict[str, Any]:
    settings = get_settings()
    raw_body = await request.body()
    expected = _twilio_signature(raw_body, settings.twilio_auth_token)
    if not hmac.compare_digest(request.headers.get("X-Twilio-Signature", ""), expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid twilio signature")

    message = f"Inbound call ({payload.call_status or 'received'}) from {payload.from_number}"
    lead, contact = ingest_lead(
        name=payload.from_number,
        email=None,
        phone=payload.from_number,
        message=message,
        source="twilio_voice",
        inbound_type=InteractionType.CALL_IN,
        channel_id=payload.call_sid,
    )
    logger.info("twilio-voice-ingested", contact_id=str(contact.id), lead_id=str(lead.id))
    return {"status": "accepted", "lead_id": str(lead.id)}


__all__ = ["router"]
