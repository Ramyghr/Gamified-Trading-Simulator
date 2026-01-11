"""aa

Revision ID: 77b41ccd4fb5
Revises: 23e1c992bc91
Create Date: 2025-12-04 00:44:03.777226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77b41ccd4fb5'
down_revision: Union[str, None] = '23e1c992bc91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
