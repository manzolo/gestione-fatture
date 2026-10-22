"""Add tipo_seduta to fattura (singola / coppia)

Revision ID: f2a4c6e8b0d2
Revises: d9e1f3a5b7c9
Create Date: 2026-10-22 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a4c6e8b0d2'
down_revision: Union[str, Sequence[str], None] = 'd9e1f3a5b7c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add session type to fattura; existing invoices become 'singola'."""
    op.add_column('fattura', sa.Column('tipo_seduta', sa.String(20), nullable=False, server_default='singola'))


def downgrade() -> None:
    """Remove session type from fattura."""
    op.drop_column('fattura', 'tipo_seduta')
