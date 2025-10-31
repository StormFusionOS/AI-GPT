"""Routes for browsing backup archives and media artifacts."""

from __future__ import annotations

import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import require_admin_role
from app.core.config import settings

router = APIRouter(prefix='/media', tags=['media'])

RootType = Literal['media', 'backup']

ROOT_DIRECTORIES: dict[RootType, Path] = {
    'media': Path(settings.media_root).expanduser().resolve(),
    'backup': Path(settings.backup_root).expanduser().resolve(),
}

for path in ROOT_DIRECTORIES.values():
    path.mkdir(parents=True, exist_ok=True)


class Breadcrumb(BaseModel):
    name: str
    path: str


class MediaEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified_at: datetime
    mime_type: str | None = None


class MediaListResponse(BaseModel):
    root: RootType
    path: str
    breadcrumbs: list[Breadcrumb]
    entries: list[MediaEntry]


def _resolve_root(root: RootType) -> Path:
    try:
        return ROOT_DIRECTORIES[root]
    except KeyError as exc:  # pragma: no cover - guarded by Literal typing
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unknown root directory') from exc


def _normalize_subpath(subpath: str | None) -> Path:
    if not subpath:
        return Path('.')
    clean = subpath.strip('/ ')
    candidate = Path(clean) if clean else Path('.')
    if any(part in {'..', '.'} for part in candidate.parts):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Path traversal is not permitted')
    return candidate


def _resolve_path(root: RootType, relative_path: Path) -> Path:
    base = _resolve_root(root)
    candidate = (base / relative_path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid path outside allowed directory') from None
    return candidate


def _build_breadcrumbs(root: RootType, relative_path: Path) -> list[Breadcrumb]:
    crumbs: list[Breadcrumb] = [
        Breadcrumb(name='Media' if root == 'media' else 'Backups', path=''),
    ]
    if relative_path == Path('.'):
        return crumbs

    cumulative = Path('')
    for part in relative_path.parts:
        cumulative /= part
        crumbs.append(Breadcrumb(name=part, path=cumulative.as_posix()))
    return crumbs


def _serialize_entry(root: RootType, base: Path, path: Path) -> MediaEntry:
    stat = path.stat()
    relative = path.relative_to(base).as_posix()
    mime_type = mimetypes.guess_type(path.name)[0] if path.is_file() else None
    return MediaEntry(
        name=path.name,
        path=relative,
        is_dir=path.is_dir(),
        size=0 if path.is_dir() else stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        mime_type=mime_type,
    )


async def _iter_file(path: Path, chunk_size: int = 1024 * 512):
    async with aiofiles.open(path, 'rb') as file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk


@router.get('/list', response_model=MediaListResponse)
async def list_media(
    root: RootType = Query('media'),
    path: str | None = Query(default=None),
    _: None = Depends(require_admin_role),
) -> MediaListResponse:
    """Return the contents of a directory inside the allowed media roots."""

    relative_path = _normalize_subpath(path)
    target_path = _resolve_path(root, relative_path)
    if not target_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Directory not found')
    if not target_path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Path is not a directory')

    base = _resolve_root(root)
    entries = sorted((_serialize_entry(root, base, child) for child in target_path.iterdir()), key=lambda entry: (not entry.is_dir, entry.name.lower()))

    return MediaListResponse(
        root=root,
        path='' if relative_path in {Path('.'), Path()} else relative_path.as_posix(),
        breadcrumbs=_build_breadcrumbs(root, relative_path),
        entries=entries,
    )


@router.get('/file/{file_path:path}')
async def get_media_file(
    file_path: str,
    root: RootType = Query('media'),
    _: None = Depends(require_admin_role),
):
    """Stream a file from the media or backup directory."""

    relative_path = _normalize_subpath(file_path)
    target_path = _resolve_path(root, relative_path)
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='File not found')

    media_type = mimetypes.guess_type(target_path.name)[0] or 'application/octet-stream'
    headers = {
        'Content-Disposition': f'attachment; filename="{quote(target_path.name)}"'
    }

    return StreamingResponse(_iter_file(target_path), media_type=media_type, headers=headers)

