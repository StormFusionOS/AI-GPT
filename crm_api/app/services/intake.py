"""Inbound lead ingestion utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import structlog

from ..db import (
    ensure_lead,
    get_auto_reply_rule,
    record_interaction,
    upsert_contact_record,
)
from ..models import AutoReplyChannel, Contact, InteractionType, Lead

logger = structlog.get_logger(__name__)


def _choose_channel(contact: Contact) -> Optional[AutoReplyChannel]:
    if contact.phone:
        return AutoReplyChannel.SMS
    if contact.email:
        return AutoReplyChannel.EMAIL
    return None


def _render_reply(channel: AutoReplyChannel, contact: Contact, now: Optional[datetime] = None) -> Optional[str]:
    rule = get_auto_reply_rule(channel)
    if not rule or not rule.enabled:
        return None
    now = now or datetime.utcnow()
    hour = now.hour
    in_hours = rule.business_hours_start <= hour < rule.business_hours_end
    template = rule.template if in_hours else rule.after_hours_template
    try:
        return template.format(name=contact.name)
    except Exception:  # pragma: no cover - defensive fallback
        logger.warning("auto-reply-template-error", channel=channel.value)
        return template


def ingest_lead(
    *,
    name: str,
    email: str | None,
    phone: str | None,
    message: str,
    source: str,
    inbound_type: InteractionType,
    channel_id: str | None = None,
    now: Optional[datetime] = None,
) -> tuple[Lead, Contact]:
    """Upsert contact, ensure a lead exists, and capture inbound + auto reply interactions."""

    contact = upsert_contact_record(name=name or "Prospect", email=email, phone=phone)
    lead = ensure_lead(contact.id, source)
    record_interaction(lead.id, contact.id, inbound_type, message, channel_id=channel_id)

    channel = _choose_channel(contact)
    if channel == AutoReplyChannel.SMS:
        reply = _render_reply(channel, contact, now=now)
        if reply:
            record_interaction(
                lead.id,
                contact.id,
                InteractionType.SMS_OUT,
                reply,
                channel_id="AUTO_REPLY_SMS",
            )
    elif channel == AutoReplyChannel.EMAIL:
        reply = _render_reply(channel, contact, now=now)
        if reply:
            record_interaction(
                lead.id,
                contact.id,
                InteractionType.EMAIL_OUT,
                reply,
                channel_id="AUTO_REPLY_EMAIL",
            )

    return lead, contact
