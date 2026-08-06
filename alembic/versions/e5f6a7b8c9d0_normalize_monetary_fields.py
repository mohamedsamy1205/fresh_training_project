"""Normalize monetary fields precision across database tables

Revision ID: e5f6a7b8c9d0
Revises: d92bb0d3875f
Create Date: 2026-08-06 10:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd92bb0d3875f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade migration strategy:
    1. Standardizes numeric precision to NUMERIC(18, 4) across all monetary fields.
    2. Cleans up any potential malformed or unrounded values in existing tables.
    """
    # 1. Wallets table balance
    op.execute("UPDATE wallets SET balance = ROUND(balance::numeric, 4) WHERE balance IS NOT NULL;")
    op.alter_column(
        'wallets',
        'balance',
        type_=sa.Numeric(18, 4),
        existing_type=sa.Numeric(12, 2),
        nullable=False
    )

    # 2. Transactions table amount
    op.execute("UPDATE transactions SET amount = ROUND(amount::numeric, 4) WHERE amount IS NOT NULL;")
    op.alter_column(
        'transactions',
        'amount',
        type_=sa.Numeric(18, 4),
        existing_type=sa.Numeric(12, 2),
        nullable=False
    )

    # 3. Ledger entries table amount & balance_after
    op.execute("""
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ledger_entries') THEN
            UPDATE ledger_entries SET amount = ROUND(amount::numeric, 4), balance_after = ROUND(balance_after::numeric, 4);
        END IF;
    """)

    # 4. Projects table initial_amount & final_amount
    op.execute("""
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
            UPDATE projects SET initial_amount = ROUND(initial_amount::numeric, 4);
            UPDATE projects SET final_amount = ROUND(final_amount::numeric, 4) WHERE final_amount IS NOT NULL;
        END IF;
    """)


def downgrade() -> None:
    """Downgrade migration strategy."""
    op.alter_column(
        'wallets',
        'balance',
        type_=sa.Numeric(12, 2),
        existing_type=sa.Numeric(18, 4),
        nullable=False
    )

    op.alter_column(
        'transactions',
        'amount',
        type_=sa.Numeric(12, 2),
        existing_type=sa.Numeric(18, 4),
        nullable=False
    )
