"""create_watchlist_tables

Revision ID: 52d688452a41
Revises: 
Create Date: 2025-10-17 16:25:48.357515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52d688452a41'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_watchlists_user_id', 'watchlists', ['user_id'])

    # Create watchlist_items table
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('asset_type', sa.String(length=20), server_default='stock', nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('watchlist_id', 'symbol', name='uix_watchlist_symbol')
    )
    op.create_index('idx_watchlist_items_watchlist_id', 'watchlist_items', ['watchlist_id'])
    op.create_index('idx_watchlist_items_symbol', 'watchlist_items', ['symbol'])

    # Create trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_watchlists_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER watchlists_updated_at
        BEFORE UPDATE ON watchlists
        FOR EACH ROW
        EXECUTE FUNCTION update_watchlists_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS watchlists_updated_at ON watchlists;")
    op.execute("DROP FUNCTION IF EXISTS update_watchlists_updated_at();")
    
    # Drop tables (cascade will handle foreign keys)
    op.drop_index('idx_watchlist_items_symbol', table_name='watchlist_items')
    op.drop_index('idx_watchlist_items_watchlist_id', table_name='watchlist_items')
    op.drop_table('watchlist_items')
    
    op.drop_index('idx_watchlists_user_id', table_name='watchlists')
    op.drop_table('watchlists')
