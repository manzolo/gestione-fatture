"""Add optional luogo_nascita to cliente

Revision ID: c8d0e2f4a6b8
Revises: b7c9d1e2f3a4
Create Date: 2026-07-03 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d0e2f4a6b8'
down_revision: Union[str, Sequence[str], None] = 'b7c9d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional birth place to cliente (used by the giustificativo)."""
    op.add_column('cliente', sa.Column('luogo_nascita', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove birth place from cliente."""
    op.drop_column('cliente', 'luogo_nascita')
