"""operator_feedback table

Revision ID: 0003_operator_feedback
Revises: 0002_bounty_columns
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_operator_feedback"
down_revision: str | Sequence[str] | None = "0002_bounty_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "operator_feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("operator_address", sa.String(64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.String(2048), nullable=True),
        sa.Column("onchain_tx_hash", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_operator_feedback_scan_id", "operator_feedback", ["scan_id"])
    op.create_index(
        "ix_operator_feedback_operator_address",
        "operator_feedback",
        ["operator_address"],
    )
    op.create_index(
        "ix_operator_feedback_onchain_tx_hash",
        "operator_feedback",
        ["onchain_tx_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_operator_feedback_onchain_tx_hash", table_name="operator_feedback")
    op.drop_index("ix_operator_feedback_operator_address", table_name="operator_feedback")
    op.drop_index("ix_operator_feedback_scan_id", table_name="operator_feedback")
    op.drop_table("operator_feedback")
