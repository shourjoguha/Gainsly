"""drop_migrated_json_columns

Revision ID: feab32325bef
Revises: 20a4abf61a67
Create Date: 2026-01-23 01:02:38.976970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'feab32325bef'
down_revision: Union[str, Sequence[str], None] = '20a4abf61a67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop migrated JSON columns from sessions
    op.drop_column('sessions', 'warmup_json')
    op.drop_column('sessions', 'main_json')
    op.drop_column('sessions', 'accessory_json')
    op.drop_column('sessions', 'finisher_json')
    op.drop_column('sessions', 'cooldown_json')

    # Drop migrated columns from movements
    op.drop_column('movements', 'secondary_muscles')
    op.drop_column('movements', 'discipline_tags')
    op.drop_column('movements', 'equipment_tags')
    op.drop_column('movements', 'tags')
    op.drop_column('movements', 'coaching_cues')
    op.drop_column('movements', 'primary_discipline')


def downgrade() -> None:
    """Downgrade schema."""
    # Add columns back (nullable)
    op.add_column('sessions', sa.Column('cooldown_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('sessions', sa.Column('finisher_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('sessions', sa.Column('accessory_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('sessions', sa.Column('main_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('sessions', sa.Column('warmup_json', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))

    op.add_column('movements', sa.Column('primary_discipline', sa.VARCHAR(length=50), server_default=sa.text("'All'::character varying"), autoincrement=False, nullable=False))
    op.add_column('movements', sa.Column('coaching_cues', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('movements', sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('movements', sa.Column('equipment_tags', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('movements', sa.Column('discipline_tags', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('movements', sa.Column('secondary_muscles', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
