"""CRUD API endpoints for managing CRM contacts (test scaffolding)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas import ContactCreate, ContactRead, ContactUpdate
from app.services.contact_service import ContactService

router = APIRouter(prefix='/contacts', tags=['contacts'])


def _get_service(session: Session = Depends(get_db_session)) -> ContactService:
    return ContactService(session)


@router.get('/', response_model=list[ContactRead])
async def list_contacts(service: ContactService = Depends(_get_service)) -> list[ContactRead]:
    return service.list_contacts()


@router.post('/', response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate, service: ContactService = Depends(_get_service)
) -> ContactRead:
    try:
        return service.create_contact(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get('/{contact_id}', response_model=ContactRead)
async def get_contact(contact_id: str, service: ContactService = Depends(_get_service)) -> ContactRead:
    try:
        return service.get_contact(contact_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found') from exc


@router.put('/{contact_id}', response_model=ContactRead)
async def update_contact(
    contact_id: str, payload: ContactUpdate, service: ContactService = Depends(_get_service)
) -> ContactRead:
    if not payload.model_dump(exclude_none=True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No changes provided')
    try:
        return service.update_contact(contact_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: str, service: ContactService = Depends(_get_service)) -> None:
    try:
        service.delete_contact(contact_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found') from exc
    return None
