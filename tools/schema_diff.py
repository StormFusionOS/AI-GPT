"""Utility to detect schema drift between metadata and the live database."""
from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from importlib import import_module
from typing import Iterator, Type

from alembic.autogenerate import api as autogen
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import DeclarativeBase

SERVICE_MAP: dict[str, dict[str, str]] = {
    "crm": {
        "settings": "crm_api.app.core.config",
        "getter": "get_settings",
        "models": "crm_api.app.db_models",
        "base": "CRMBase",
        "schema": "crm",
    },
    "ops": {
        "settings": "ops_api.app.core.config",
        "getter": "get_settings",
        "models": "ops_api.app.db_models",
        "base": "OpsBase",
        "schema": "ops",
    },
}


@contextmanager
def _schema_scope(base: Type[DeclarativeBase], connection: Connection, schema: str | None) -> Iterator[None]:
    tables = list(base.metadata.tables.values())
    previous = {table: table.schema for table in tables}
    try:
        effective_schema = schema if connection.dialect.name != "sqlite" else None
        if effective_schema:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{effective_schema}"'))
        for table in tables:
            table.schema = effective_schema
        if effective_schema:
            connection.execute(text(f'SET search_path TO "{effective_schema}"'))
        yield
    finally:
        for table in tables:
            table.schema = previous[table]


def _load_base(service: str) -> Type[DeclarativeBase]:
    info = SERVICE_MAP[service]
    module = import_module(info["models"])
    return getattr(module, info["base"])


def _load_settings(service: str):
    info = SERVICE_MAP[service]
    module = import_module(info["settings"])
    getter = getattr(module, info["getter"])
    return getter()


def check_service(service: str) -> bool:
    settings = _load_settings(service)
    base = _load_base(service)
    engine = create_engine(settings.database_url)
    has_drift = False
    with engine.connect() as connection:
        schema = SERVICE_MAP[service]["schema"]
        with _schema_scope(base, connection, schema):
            context = MigrationContext.configure(
                connection,
                opts={"compare_type": True, "target_metadata": base.metadata},
            )
            differences = autogen.compare_metadata(context, base.metadata)
            if differences:
                has_drift = True
                for diff in differences:
                    print(f"[{service}] drift detected: {diff}")
    engine.dispose()
    return not has_drift


def main() -> int:
    parser = argparse.ArgumentParser(description="Check database schema drift")
    parser.add_argument(
        "--service",
        choices=sorted(SERVICE_MAP.keys()),
        action="append",
        help="Service to check. Default checks all.",
    )
    args = parser.parse_args()

    services = args.service or sorted(SERVICE_MAP.keys())
    ok = True
    for service in services:
        if not check_service(service):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
