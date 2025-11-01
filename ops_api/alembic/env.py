"""Alembic environment configuration for ops API."""
from __future__ import annotations

from contextlib import contextmanager
from logging.config import fileConfig
from typing import Iterator

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine import Connection

from app.core.config import get_settings
from app.db_models import OpsBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


@contextmanager
def _schema_scope(connection: Connection | None, schema: str | None) -> Iterator[None]:
    tables = list(OpsBase.metadata.tables.values())
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
    url = config.get_main_option("sqlalchemy.url")
    schema = "ops" if not url.startswith("sqlite") else None
    with _schema_scope(None, schema):
        context.configure(
            url=url,
            target_metadata=OpsBase.metadata,
            literal_binds=True,
            compare_type=True,
            version_table_schema=schema,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        schema = "ops" if connection.dialect.name != "sqlite" else None
        with _schema_scope(connection, schema):
            context.configure(
                connection=connection,
                target_metadata=OpsBase.metadata,
                compare_type=True,
                version_table_schema=schema,
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
