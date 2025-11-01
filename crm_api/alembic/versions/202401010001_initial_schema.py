"""Initial CRM schema"""
from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa

revision = "202401010001"
down_revision = None
branch_labels = None
depends_on = None


def _schema() -> str | None:
    if context.get_context().dialect.name == "sqlite":
        return None
    return "crm"


def upgrade() -> None:
    schema = _schema()
    role_enum = sa.Enum(
        "SALES",
        "SALES_MANAGER",
        "OWNER",
        "CLIENT",
        name="user_role",
        schema="crm" if schema else None,
    )
    lead_enum = sa.Enum(
        "NEW",
        "CONTACTED",
        "QUALIFIED",
        "WON",
        "LOST",
        name="lead_status",
        schema="crm" if schema else None,
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("crm.users.id") if schema else sa.ForeignKey("users.id")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_index("ix_contacts_email", "contacts", ["email"], unique=True, schema=schema, postgresql_where=sa.text("email IS NOT NULL") if schema else None)
    op.create_table(
        "leads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("contact_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=True),
        sa.Column("status", lead_enum, nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("estimated_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema,
    )
    op.create_foreign_key("leads_contact_id_fkey", "leads", "contacts", ["contact_id"], ["id"], source_schema=schema, referent_schema=schema)
    op.create_foreign_key("leads_owner_id_fkey", "leads", "users", ["owner_id"], ["id"], source_schema=schema, referent_schema=schema)


def downgrade() -> None:
    schema = _schema()
    op.drop_constraint("leads_owner_id_fkey", "leads", schema=schema, type_="foreignkey")
    op.drop_constraint("leads_contact_id_fkey", "leads", schema=schema, type_="foreignkey")
    op.drop_table("leads", schema=schema)
    op.drop_index("ix_contacts_email", table_name="contacts", schema=schema)
    op.drop_table("contacts", schema=schema)
    op.drop_table("users", schema=schema)
    if schema:
        op.execute(sa.text("DROP TYPE IF EXISTS crm.lead_status"))
        op.execute(sa.text("DROP TYPE IF EXISTS crm.user_role"))
