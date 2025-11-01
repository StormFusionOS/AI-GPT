"""Expand ops schema with scheduler and automation tables"""
from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa

revision = "202401020001"
down_revision = "202401010001"
branch_labels = None
depends_on = None


def _schema() -> str | None:
    if context.get_context().dialect.name == "sqlite":
        return None
    return "ops"


def upgrade() -> None:
    schema = _schema()
    op.add_column(
        "task_runs",
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        schema=schema,
    )
    op.create_index(
        "ix_task_runs_idempotency",
        "task_runs",
        ["idempotency_key"],
        unique=False,
        schema=schema,
    )
    op.create_table(
        "anomalies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("page_id", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("proposed_actions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_table(
        "scheduler_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("crontab", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("anomaly_id", sa.Integer(), nullable=True),
        schema=schema,
    )
    op.create_foreign_key(
        "suggestions_anomaly_id_fkey",
        "suggestions",
        "anomalies",
        ["anomaly_id"],
        ["id"],
        ondelete="SET NULL",
        source_schema=schema,
        referent_schema=schema,
    )
    op.create_table(
        "change_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("anomaly_id", sa.Integer(), nullable=True),
        schema=schema,
    )
    op.create_foreign_key(
        "change_log_anomaly_id_fkey",
        "change_log",
        "anomalies",
        ["anomaly_id"],
        ["id"],
        ondelete="SET NULL",
        source_schema=schema,
        referent_schema=schema,
    )
    op.create_table(
        "file_integrity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.String(length=512), nullable=False, unique=True),
        sa.Column("sha256", sa.String(length=128), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_table(
        "backup_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_type", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("verify_ok", sa.Boolean(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        schema=schema,
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )


def downgrade() -> None:
    schema = _schema()
    op.drop_table("alerts", schema=schema)
    op.drop_table("backup_runs", schema=schema)
    op.drop_table("file_integrity", schema=schema)
    op.drop_constraint("change_log_anomaly_id_fkey", "change_log", schema=schema, type_="foreignkey")
    op.drop_table("change_log", schema=schema)
    op.drop_constraint("suggestions_anomaly_id_fkey", "suggestions", schema=schema, type_="foreignkey")
    op.drop_table("suggestions", schema=schema)
    op.drop_table("scheduler_configs", schema=schema)
    op.drop_table("anomalies", schema=schema)
    op.drop_index("ix_task_runs_idempotency", table_name="task_runs", schema=schema)
    op.drop_column("task_runs", "idempotency_key", schema=schema)
*** End
