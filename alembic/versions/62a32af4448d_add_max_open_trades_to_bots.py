"""add_max_open_trades_to_bots

Revision ID: 62a32af4448d
Revises: ffb88e5ae6f0
Create Date: 2025-12-02 23:25:24.276480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62a32af4448d'
down_revision: Union[str, None] = 'ffb88e5ae6f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add max_open_trades column with default value of 1
    op.add_column('bots', sa.Column('max_open_trades', sa.Integer(), nullable=False, server_default='1'))
    
    # Add check constraint to ensure value is positive
    op.create_check_constraint(
        'ck_bots_max_open_trades_positive',
        'bots',
        sa.text('max_open_trades >= 1')
    )


def downgrade():
    # Remove check constraint
    op.drop_constraint('ck_bots_max_open_trades_positive', 'bots', type_='check')
    
    # Remove column
    op.drop_column('bots', 'max_open_trades')