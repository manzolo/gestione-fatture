"""Costi ricorrenti

Revision ID: b7c9d1e2f3a4
Revises: a1b2c3d4e5f6
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c9d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'costo_ricorrente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('descrizione', sa.String(length=255), nullable=False),
        sa.Column('totale', sa.Float(), nullable=False),
        sa.Column('frequenza', sa.String(length=20), nullable=False),
        sa.Column('giorno_scadenza', sa.Integer(), nullable=False),
        sa.Column('data_inizio', sa.Date(), nullable=False),
        sa.Column('data_fine', sa.Date(), nullable=True),
        sa.Column('pagato_default', sa.Boolean(), nullable=True),
        sa.Column('attivo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('costo', sa.Column('ricorrenza_id', sa.Integer(), nullable=True))
    op.add_column('costo', sa.Column('periodo_riferimento', sa.String(length=7), nullable=True))
    op.create_foreign_key(
        'fk_costo_ricorrenza_id_costo_ricorrente',
        'costo',
        'costo_ricorrente',
        ['ricorrenza_id'],
        ['id']
    )
    op.create_unique_constraint(
        'uq_costo_ricorrenza_periodo',
        'costo',
        ['ricorrenza_id', 'periodo_riferimento']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_costo_ricorrenza_periodo', 'costo', type_='unique')
    op.drop_constraint('fk_costo_ricorrenza_id_costo_ricorrente', 'costo', type_='foreignkey')
    op.drop_column('costo', 'periodo_riferimento')
    op.drop_column('costo', 'ricorrenza_id')
    op.drop_table('costo_ricorrente')
