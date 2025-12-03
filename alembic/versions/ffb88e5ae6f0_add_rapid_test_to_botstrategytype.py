"""add_rapid_test_to_botstrategytype

Revision ID: ffb88e5ae6f0
Revises: f688424e2f02
Create Date: 2025-12-02 22:42:46.387844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffb88e5ae6f0'
down_revision: Union[str, None] = 'f688424e2f02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # For PostgreSQL, add the new enum value
    op.execute("ALTER TYPE botstrategytype ADD VALUE 'RAPID_TEST'")
    
    # Or if using a different database, you might need to:
    # 1. Create a new type with the added value
    # 2. Change the column to use the new type
    # 3. Drop the old type


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values easily
    # You might need to create a new type without RAPID_TEST
    # and migrate data
    
    # For PostgreSQL 12+, you can use:
    op.execute("DELETE FROM bots WHERE strategy_type = 'RAPID_TEST'")
    
    # Create a new type without RAPID_TEST
    op.execute("CREATE TYPE botstrategytype_new AS ENUM ('MEAN_REVERSION', 'BREAKOUT', 'TREND_FOLLOWING')")
    
    # Change column type
    op.execute("""
        ALTER TABLE bots 
        ALTER COLUMN strategy_type TYPE botstrategytype_new 
        USING strategy_type::text::botstrategytype_new
    """)
    
    # Drop old type and rename new type
    op.execute("DROP TYPE botstrategytype")
    op.execute("ALTER TYPE botstrategytype_new RENAME TO botstrategytype")

