"""Alembic environment configuration for the CRM schema."""
from __future__ import annotations

from contextlib import contextmanager
from logging.config import fileConfig
from typing import Iterator

from alembic import context
from sqlalchemy import engine_from_config, text
from sqlalchemy.engine import Connection

from app.core.config import get_settings
from app.db_models import CRMBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


@contextmanager
def _schema_scope(connection: Connection | None, schema: str | None) -> Iterator[None]:
    """Temporarily adjusts metadata schema for the given dialect."""

    tables = list(CRMBase.metadata.tables.values())
    previous = {table: table.schema for table in tables}
    try:
        if connection is not None and schema and connection.dialect.name != "sqlite":
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        for table in tables:
            table.schema = schema
        yield
    finally:
        for table in tables:
            table.schema = previous[table]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = config.get_main_option("sqlalchemy.url")
    schema = "crm" if not url.startswith("sqlite") else None
    with _schema_scope(None, schema):
        context.configure(
            url=url,
            target_metadata=CRMBase.metadata,
            literal_binds=True,
            compare_type=True,
            version_table_schema=schema,
        )
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.")

    with connectable.connect() as connection:
        schema = "crm" if connection.dialect.name != "sqlite" else None
        with _schema_scope(connection, schema):
            context.configure(
                connection=connection,
                target_metadata=CRMBase.metadata,
                compare_type=True,
                version_table_schema=schema,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
