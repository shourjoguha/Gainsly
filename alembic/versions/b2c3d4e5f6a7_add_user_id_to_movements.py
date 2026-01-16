"""Add user_id to movements

Revision ID: b2c3d4e5f6a7
Revises: 6180f4706b14
Create Date: 2026-01-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '6180f4706b14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to movements table
    op.add_column('movements', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_movements_user_id'), 'movements', ['user_id'], unique=False)
    op.create_foreign_key(None, 'movements', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Remove user_id column from movements table
    op.drop_constraint(None, 'movements', type_='foreignkey')
    op.drop_index(op.f('ix_movements_user_id'), table_name='movements')
    op.drop_column('movements', 'user_id')
