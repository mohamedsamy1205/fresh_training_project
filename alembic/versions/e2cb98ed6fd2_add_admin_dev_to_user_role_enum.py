"""add admin_dev to user_role enum

Revision ID: e2cb98ed6fd2
Revises: 9f0bedf50203
Create Date: 2026-08-02 08:12:10.788843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2cb98ed6fd2'
down_revision: Union[str, Sequence[str], None] = '9f0bedf50203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'admin_dev'")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
