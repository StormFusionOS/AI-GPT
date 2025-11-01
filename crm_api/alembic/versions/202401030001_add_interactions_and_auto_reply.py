"""Add interactions and auto reply rules tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202401030001_add_interactions"
down_revision = "202401010001_initial_schema"
branch_labels = None
depends_on = None


INTERACTION_TYPE = sa.Enum(
    "SMS_IN",
    "SMS_OUT",
    "EMAIL_IN",
    "EMAIL_OUT",
    "CALL_IN",
    "CALL_OUT",
    "FB_MSG",
    "IG_DM",
    name="interaction_type",
    schema="crm",
)

AUTO_REPLY_CHANNEL = sa.Enum("SMS", "EMAIL", name="auto_reply_channel", schema="crm")


def upgrade() -> None:
    INTERACTION_TYPE.create(op.get_bind(), checkfirst=True)
    AUTO_REPLY_CHANNEL.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "interactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lead_id", sa.String(length=36), sa.ForeignKey("crm.leads.id", ondelete="SET NULL")),
        sa.Column("contact_id", sa.String(length=36), sa.ForeignKey("crm.contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_type", INTERACTION_TYPE, nullable=False),
        sa.Column("channel_id", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="crm",
    )

    op.create_table(
        "auto_reply_rules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("channel", AUTO_REPLY_CHANNEL, nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("after_hours_template", sa.Text(), nullable=False),
        sa.Column("business_hours_start", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("business_hours_end", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        schema="crm",
    )

    op.create_index("ix_crm_interactions_lead_id", "interactions", ["lead_id"], schema="crm")
    op.create_index("ix_crm_interactions_contact_id", "interactions", ["contact_id"], schema="crm")


def downgrade() -> None:
    op.drop_index("ix_crm_interactions_contact_id", table_name="interactions", schema="crm")
    op.drop_index("ix_crm_interactions_lead_id", table_name="interactions", schema="crm")
    op.drop_table("auto_reply_rules", schema="crm")
    op.drop_table("interactions", schema="crm")
    AUTO_REPLY_CHANNEL.drop(op.get_bind(), checkfirst=True)
    INTERACTION_TYPE.drop(op.get_bind(), checkfirst=True)
