"""Webhook payload schemas."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FacebookField(BaseModel):
    name: str
    values: List[str]


class FacebookEntry(BaseModel):
    id: str
    field_data: List[FacebookField]


class FacebookLeadPayload(BaseModel):
    entry: List[FacebookEntry]


class GoogleLeadPayload(BaseModel):
    lead_id: str = Field(..., alias="leadId")
    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    customer_id: Optional[str] = Field(default=None, alias="customerId")
    user_identifier: Optional[str] = Field(default=None, alias="userIdentifier")
    lead_data: dict


class TwilioSMSPayload(BaseModel):
    from_number: str = Field(..., alias="From")
    to_number: str = Field(..., alias="To")
    body: str = Field(..., alias="Body")
    message_sid: str = Field(..., alias="MessageSid")


class TwilioVoicePayload(BaseModel):
    from_number: str = Field(..., alias="From")
    call_sid: str = Field(..., alias="CallSid")
    call_status: Optional[str] = Field(default=None, alias="CallStatus")


__all__ = [
    "FacebookLeadPayload",
    "GoogleLeadPayload",
    "TwilioSMSPayload",
    "TwilioVoicePayload",
]
