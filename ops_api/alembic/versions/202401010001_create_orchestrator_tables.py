"""create orchestrator tables"""
from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa

revision = "202401010001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = "ops"
    if context.get_context().dialect.name == "sqlite":
        schema = None
    op.create_table(
        "service_health",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service", sa.String(length=100), nullable=False, unique=True),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        schema=schema,
    )
    op.create_table(
        "task_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("task", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        schema=schema,
    )


def downgrade() -> None:
    schema = "ops"
    if context.get_context().dialect.name == "sqlite":
        schema = None
    op.drop_table("task_runs", schema=schema)
    op.drop_table("service_health", schema=schema)
