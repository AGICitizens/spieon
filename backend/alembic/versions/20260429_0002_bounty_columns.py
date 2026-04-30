"""bounty payout columns on findings

Revision ID: 0002_bounty_columns
Revises: 0001_initial
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_bounty_columns"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "findings",
        sa.Column("bounty_recipient", sa.String(64), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("bounty_amount_usdc", sa.Numeric(18, 6), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("bounty_tx_hash", sa.String(128), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("bounty_paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_findings_bounty_tx_hash", "findings", ["bounty_tx_hash"]
    )


def downgrade() -> None:
    op.drop_index("ix_findings_bounty_tx_hash", table_name="findings")
    op.drop_column("findings", "bounty_paid_at")
    op.drop_column("findings", "bounty_tx_hash")
    op.drop_column("findings", "bounty_amount_usdc")
    op.drop_column("findings", "bounty_recipient")
