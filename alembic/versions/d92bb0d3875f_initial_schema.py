"""initial schema

Revision ID: d92bb0d3875f
Revises: 
Create Date: 2026-08-03 08:37:29.232894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd92bb0d3875f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 🔹 users table
    op.create_table(
        'users',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=True),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('email', sa.VARCHAR(), nullable=False),
        sa.Column('phone_number', sa.VARCHAR(), nullable=True),
        sa.Column('provider', sa.VARCHAR(), nullable=True),
        sa.Column('hashed_password', sa.VARCHAR(), nullable=True),
        sa.Column(
            'role',
            postgresql.ENUM('admin', 'admin_dev', 'investor', name='userrole'),
            nullable=True
        ),
        sa.Column('age', sa.INTEGER(), nullable=True),
        sa.Column('is_pending', sa.BOOLEAN(), nullable=True),
        sa.Column('is_locked', sa.BOOLEAN(), nullable=True),
        sa.Column(
            'created_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        ),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_users_uuid', 'users', ['uuid'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 🔹 wallets table
    op.create_table(
        'wallets',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('balance', sa.NUMERIC(12, 2), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.uuid']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_wallets_uuid', 'wallets', ['uuid'], unique=True)
    op.create_index('ix_wallets_id', 'wallets', ['id'], unique=False)

    # 🔹 transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=False),
        sa.Column('wallet_id', sa.UUID(), nullable=True),
        sa.Column('amount', sa.NUMERIC(12, 2), nullable=False),
        sa.Column(
            'type',
            postgresql.ENUM('DEPOSIT', 'WITHDRAW', 'TRANSFER', name='transactiontype'),
            nullable=True
        ),
        sa.Column(
            'status',
            postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='transactionstatus'),
            nullable=True
        ),
        sa.Column('description', sa.VARCHAR(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['sender_id'], ['users.uuid']),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.uuid']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_transactions_uuid', 'transactions', ['uuid'], unique=True)
    op.create_index('ix_transactions_id', 'transactions', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index('ix_transactions_id', table_name='transactions')
    op.drop_index('ix_transactions_uuid', table_name='transactions')
    op.drop_table('transactions')

    op.drop_index('ix_wallets_id', table_name='wallets')
    op.drop_index('ix_wallets_uuid', table_name='wallets')
    op.drop_table('wallets')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_uuid', table_name='users')
    op.drop_table('users')