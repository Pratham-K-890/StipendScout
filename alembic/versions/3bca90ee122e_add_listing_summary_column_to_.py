"""add listing_summary column to applications

Revision ID: 3bca90ee122e
Revises: bda9f6401245
Create Date: 2026-09-15 22:11:50.573385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3bca90ee122e'
down_revision: Union[str, Sequence[str], None] = 'bda9f6401245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Note: autogenerate also proposed dropping the checkpoint_* tables —
    # those are owned/managed by LangGraph's PostgresSaver, not our
    # SQLAlchemy models, so autogenerate sees them as "unknown" and wants
    # to remove them. Stripped out by hand; only the real change remains.
    op.add_column('applications', sa.Column('listing_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('applications', 'listing_summary')
