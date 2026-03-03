"""Add STS fields to fattura and cliente

Revision ID: a1b2c3d4e5f6
Revises: e52bda5ede63
Create Date: 2026-03-03 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e52bda5ede63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add STS-related fields."""
    op.add_column('fattura', sa.Column('inviata_sts', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('fattura', sa.Column('protocollo_sts', sa.String(100), nullable=True))
    op.add_column('fattura', sa.Column('data_invio_sts', sa.DateTime(), nullable=True))
    op.add_column('cliente', sa.Column('flag_opposizione', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Remove STS-related fields."""
    op.drop_column('fattura', 'inviata_sts')
    op.drop_column('fattura', 'protocollo_sts')
    op.drop_column('fattura', 'data_invio_sts')
    op.drop_column('cliente', 'flag_opposizione')
