"""zenb

Revision ID: 23e1c992bc91
Revises: 2cf5e5070eb1
Create Date: 2025-12-04 00:43:35.325913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23e1c992bc91'
down_revision: Union[str, None] = '2cf5e5070eb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
