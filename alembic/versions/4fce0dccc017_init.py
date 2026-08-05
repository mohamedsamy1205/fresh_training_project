from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = 'xxxx'
down_revision = None  # أو اللي قبله
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ledger_entries',

        sa.Column('id', sa.Integer(), primary_key=True, index=True),

        sa.Column(
            'uuid',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            index=True,
            default=uuid.uuid4
        ),

        sa.Column(
            'transaction_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('transactions.uuid'),
            nullable=False,
            index=True
        ),

        sa.Column(
            'wallet_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('wallets.uuid'),
            nullable=False,
            index=True
        ),

        sa.Column(
            'entry_type',
            sa.Enum('DEBIT', 'CREDIT', name='ledgerentrytype'),
            nullable=False
        ),

        sa.Column(
            'amount',
            sa.Numeric(18, 4),
            nullable=False
        ),

        sa.Column(
            'balance_after',
            sa.Numeric(18, 4),
            nullable=False
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    # Indexes
    op.create_index('ix_ledger_entries_uuid', 'ledger_entries', ['uuid'])
    op.create_index('ix_ledger_entries_transaction_id', 'ledger_entries', ['transaction_id'])
    op.create_index('ix_ledger_entries_wallet_id', 'ledger_entries', ['wallet_id'])


def downgrade():
    op.drop_index('ix_ledger_entries_wallet_id', table_name='ledger_entries')
    op.drop_index('ix_ledger_entries_transaction_id', table_name='ledger_entries')
    op.drop_index('ix_ledger_entries_uuid', table_name='ledger_entries')

    op.drop_table('ledger_entries')

    # drop enum
    sa.Enum(name='ledgerentrytype').drop(op.get_bind(), checkfirst=True)