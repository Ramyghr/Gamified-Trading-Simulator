"""rapid_test

Revision ID: f5d0ca34e7a7
Revises: 
Create Date: 2025-12-02 22:24:41.983499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f5d0ca34e7a7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the old ENUM type
    op.execute("ALTER TYPE gender_enum RENAME TO gender_old")

    # Create the new ENUM type
    gender = postgresql.ENUM(
        'MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY',
        name='gender'
    )
    gender.create(op.get_bind(), checkfirst=True)

    # Alter the column using safe cast
    op.execute(
        "ALTER TABLE users ALTER COLUMN gender TYPE gender USING gender::text::gender"
    )

    # Drop old ENUM
    op.execute("DROP TYPE gender_old")


def downgrade() -> None:
    # Reverse steps if needed

    # Recreate old enum
    old_gender = postgresql.ENUM(
        'MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY',
        name='gender_enum'
    )
    old_gender.create(op.get_bind(), checkfirst=True)

    # Cast back
    op.execute(
        "ALTER TABLE users ALTER COLUMN gender TYPE gender_enum USING gender::text::gender_enum"
    )

    # Drop the new enum
    op.execute("DROP TYPE gender")
