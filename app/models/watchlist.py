"""
Watchlist database models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), default="stock")
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint('watchlist_id', 'symbol', name='uix_watchlist_symbol'),
        Index('idx_watchlist_items_watchlist_id', 'watchlist_id'),
        Index('idx_watchlist_items_symbol', 'symbol'),
    )