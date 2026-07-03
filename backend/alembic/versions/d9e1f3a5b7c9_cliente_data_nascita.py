"""Add optional data_nascita to cliente

Revision ID: d9e1f3a5b7c9
Revises: c8d0e2f4a6b8
Create Date: 2026-07-03 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e1f3a5b7c9'
down_revision: Union[str, Sequence[str], None] = 'c8d0e2f4a6b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional birth date to cliente (used by the giustificativo,
    takes precedence over the date decoded from the codice fiscale)."""
    op.add_column('cliente', sa.Column('data_nascita', sa.Date(), nullable=True))


def downgrade() -> None:
    """Remove birth date from cliente."""
    op.drop_column('cliente', 'data_nascita')
