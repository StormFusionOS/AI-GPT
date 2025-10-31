"""Backup utilities for databases, vector indexes, and media assets."""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http.models import SnapshotDescription
from sqlalchemy.engine import make_url

from app.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class BackupContext:
    """Contextual information about the backup run."""

    backup_root: Path
    media_root: Path
    timestamp: str
    working_dir: Path


def _resolve_paths() -> tuple[Path, Path]:
    backup_root = Path(settings.backup_root).expanduser().resolve()
    media_root = Path(settings.media_root).expanduser().resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    media_root.mkdir(parents=True, exist_ok=True)
    return backup_root, media_root


def _database_dump_path(ctx: BackupContext) -> Path:
    return ctx.working_dir / 'database.sql'


def _qdrant_snapshot_path(ctx: BackupContext, snapshot: SnapshotDescription) -> Path:
    filename = snapshot.name if snapshot.name.endswith('.tar') else f"{snapshot.name}.tar"
    return ctx.working_dir / filename


def _media_archive_path(ctx: BackupContext) -> Path:
    return ctx.working_dir / 'media.tar.gz'


def _create_context() -> BackupContext:
    backup_root, media_root = _resolve_paths()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    working_dir = backup_root / f'backup_{timestamp}'
    working_dir.mkdir(parents=True, exist_ok=False)
    return BackupContext(backup_root=backup_root, media_root=media_root, timestamp=timestamp, working_dir=working_dir)


def _run_pg_dump(ctx: BackupContext) -> Path:
    dump_path = _database_dump_path(ctx)
    url = make_url(str(settings.database_url))
    env = os.environ.copy()
    if url.password:
        env['PGPASSWORD'] = url.password

    args = [
        'pg_dump',
        '-h',
        url.host or 'localhost',
        '-p',
        str(url.port or 5432),
        '-U',
        url.username or 'postgres',
        '-d',
        url.database or 'postgres',
        '-F',
        'p',
        '-f',
        str(dump_path),
    ]

    logger.info('backup.pg_dump.start', args=args, output=str(dump_path))
    result = subprocess.run(args, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.error('backup.pg_dump.failed', stdout=result.stdout, stderr=result.stderr)
        raise RuntimeError('pg_dump failed')

    if dump_path.stat().st_size == 0:
        raise RuntimeError('database dump is empty, aborting backup')

    logger.info('backup.pg_dump.complete', size_bytes=dump_path.stat().st_size)
    return dump_path


def _download_qdrant_snapshot(ctx: BackupContext) -> Path | None:
    client = QdrantClient(url=str(settings.qdrant_url), api_key=settings.qdrant_api_key)
    logger.info('backup.qdrant.snapshot.start', endpoint=str(settings.qdrant_url))

    snapshot = client.create_full_snapshot()
    snapshot_path = _qdrant_snapshot_path(ctx, snapshot)
    client.download_snapshot(snapshot, path=str(snapshot_path))

    if not snapshot_path.exists() or snapshot_path.stat().st_size == 0:
        raise RuntimeError('qdrant snapshot download failed')

    logger.info('backup.qdrant.snapshot.complete', size_bytes=snapshot_path.stat().st_size)
    return snapshot_path


def _archive_media(ctx: BackupContext) -> Path:
    archive_path = _media_archive_path(ctx)
    base_name = ctx.working_dir / 'media'
    if not any(ctx.media_root.iterdir()):
        logger.warning('backup.media.empty', media_root=str(ctx.media_root))
        with tarfile.open(archive_path, mode='w:gz'):
            pass
        return archive_path

    logger.info('backup.media.archive.start', media_root=str(ctx.media_root))
    shutil.make_archive(base_name=str(base_name), format='gztar', root_dir=str(ctx.media_root))
    archive_path = base_name.with_suffix('.tar.gz')
    logger.info('backup.media.archive.complete', size_bytes=archive_path.stat().st_size)
    return archive_path


def _include_configuration(ctx: BackupContext) -> list[Path]:
    files: list[Path] = []
    for candidate in (Path('.env'), Path('backend/pyproject.toml'), Path('docker-compose.yml')):
        if candidate.exists():
            destination = ctx.working_dir / candidate.name
            shutil.copy2(candidate, destination)
            files.append(destination)
            logger.info('backup.config.copied', source=str(candidate), destination=str(destination))
    return files


def _create_tarball(ctx: BackupContext, members: Iterable[Path]) -> Path:
    tar_path = ctx.backup_root / f'{ctx.working_dir.name}.tar.gz'
    logger.info('backup.tarball.start', target=str(tar_path))
    with tarfile.open(tar_path, mode='w:gz') as tar:
        for item in members:
            tar.add(item, arcname=item.name)
    logger.info('backup.tarball.complete', size_bytes=tar_path.stat().st_size)
    return tar_path


def _verify_tarball(tar_path: Path, expected_entries: Iterable[str]) -> None:
    logger.info('backup.verify.start', archive=str(tar_path))
    if tar_path.stat().st_size == 0:
        raise RuntimeError('backup archive is empty')

    with tarfile.open(tar_path, mode='r:gz') as tar:
        tar.getmembers()  # ensures archive can be read
        for entry in expected_entries:
            if entry not in tar.getnames():
                raise RuntimeError(f'expected file {entry} missing from archive')
    logger.info('backup.verify.complete')


def _rotate_archives(ctx: BackupContext, retention_count: int) -> None:
    archives = sorted(ctx.backup_root.glob('backup_*.tar.gz'), key=lambda path: path.stat().st_mtime, reverse=True)
    for stale in archives[retention_count:]:
        logger.info('backup.rotate.delete', path=str(stale))
        stale.unlink(missing_ok=True)


def perform_backup(*, dry_run: bool = False, retention_count: int | None = None) -> Path | None:
    """Run the backup workflow synchronously."""

    retention = retention_count or settings.backup_retention_count
    if dry_run:
        backup_root, media_root = _resolve_paths()
        logger.info(
            'backup.dry_run',
            backup_root=str(backup_root),
            media_root=str(media_root),
            retention_count=retention,
        )
        return None

    ctx = _create_context()
    logger.info('backup.start', backup_root=str(ctx.backup_root), media_root=str(ctx.media_root))
    created_files: list[Path] = []
    try:
        created_files.append(_run_pg_dump(ctx))
        snapshot_path = _download_qdrant_snapshot(ctx)
        if snapshot_path:
            created_files.append(snapshot_path)
        created_files.append(_archive_media(ctx))
        created_files.extend(_include_configuration(ctx))

        tar_path = _create_tarball(ctx, created_files)
        _verify_tarball(tar_path, (item.name for item in created_files))
        _rotate_archives(ctx, retention)
        logger.info('backup.success', archive=str(tar_path))
        return tar_path
    except Exception:
        logger.exception('backup.error')
        raise
    finally:
        shutil.rmtree(ctx.working_dir, ignore_errors=True)


async def perform_backup_async(*, dry_run: bool = False, retention_count: int | None = None) -> Path | None:
    """Async wrapper for running the backup job from async contexts (Celery beat, FastAPI tasks)."""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: perform_backup(dry_run=dry_run, retention_count=retention_count))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run maintenance backups for the SEO platform.')
    parser.add_argument('--dry-run', action='store_true', help='Print planned actions without executing the backup.')
    parser.add_argument(
        '--retention',
        type=int,
        default=None,
        help='Override the number of archives to retain (defaults to settings.backup_retention_count).',
    )
    return parser.parse_args()


def _configure_logging() -> None:
    try:
        is_configured = structlog.is_configured  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - structlog always provides helper in recent versions
        is_configured = lambda: False  # type: ignore[return-value]

    if not is_configured():
        structlog.configure(processors=[structlog.processors.TimeStamper(fmt='iso'), structlog.processors.JSONRenderer()])


def main() -> None:
    _configure_logging()
    args = _parse_args()
    perform_backup(dry_run=args.dry_run, retention_count=args.retention)


if __name__ == '__main__':
    main()
