"""Client-facing API endpoints used by the customer portal."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ClientContext, get_client_context
from app.schemas import (
    Appointment,
    DashboardSummary,
    Interaction,
    Invoice,
    LoginRequest,
    LoginResponse,
    MessageRequest,
    Profile,
    ProfileUpdateRequest,
    RescheduleRequest,
    PasswordChangeRequest,
)
from app.services import client_portal

router = APIRouter(prefix='/client', tags=['client-portal'])


@router.post('/auth/login', response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    try:
        client_id, profile = client_portal.authenticate(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials') from exc

    token = client_portal.issue_token(client_id)
    return LoginResponse(token=token, client_id=client_id, name=profile.name, primary_contact=profile.primary_contact)


@router.get('/dashboard', response_model=DashboardSummary)
async def fetch_dashboard(context: ClientContext = Depends(get_client_context)) -> DashboardSummary:
    """Return a personalised overview for the authenticated client."""

    return client_portal.get_dashboard_summary(context.client_id)


@router.get('/appointments', response_model=list[Appointment])
async def list_appointments(context: ClientContext = Depends(get_client_context)) -> list[Appointment]:
    return client_portal.list_appointments(context.client_id)


@router.post('/appointments/{appointment_id}/reschedule')
async def request_reschedule(
    appointment_id: str,
    request: RescheduleRequest,
    context: ClientContext = Depends(get_client_context),
) -> dict:
    return client_portal.acknowledge_reschedule_request(
        appointment_id=appointment_id,
        client_id=context.client_id,
        requested_start=request.requested_start,
        message=request.message,
    )


@router.get('/interactions', response_model=list[Interaction])
async def list_interactions(context: ClientContext = Depends(get_client_context)) -> list[Interaction]:
    return client_portal.list_interactions(context.client_id)


@router.post('/messages')
async def send_message(
    message: MessageRequest,
    context: ClientContext = Depends(get_client_context),
) -> dict:
    message_id = client_portal.record_client_message(
        client_id=context.client_id,
        channel=message.channel,
        content=message.content,
    )
    return {'id': message_id, 'status': 'queued'}


@router.get('/invoices', response_model=list[Invoice])
async def list_invoices(context: ClientContext = Depends(get_client_context)) -> list[Invoice]:
    return client_portal.list_invoices(context.client_id)


@router.get('/profile', response_model=Profile)
async def fetch_profile(context: ClientContext = Depends(get_client_context)) -> Profile:
    return client_portal.get_profile(context.client_id)


@router.patch('/profile', response_model=Profile)
async def update_profile(
    payload: ProfileUpdateRequest,
    context: ClientContext = Depends(get_client_context),
) -> Profile:
    if not payload.dict(exclude_none=True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No changes submitted')
    return client_portal.update_profile(context.client_id, **payload.dict(exclude_none=True))


@router.post('/profile/password')
async def change_password(
    payload: PasswordChangeRequest,
    context: ClientContext = Depends(get_client_context),
) -> dict:
    client_portal.change_password(context.client_id, payload.new_password)
    return {'status': 'accepted'}


@router.get('/identity')
async def get_identity(context: ClientContext = Depends(get_client_context)) -> dict:
    """Expose the authenticated client's identity for the portal bootstrap."""

    profile = client_portal.get_profile(context.client_id)
    return {
        'clientId': context.client_id,
        'role': context.role,
        'name': profile.name,
        'primaryContact': profile.primary_contact,
    }
