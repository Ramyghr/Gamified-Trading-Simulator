from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base


class UserXP(Base):
    """
    User's XP, level, coins, and badges
    """
    __tablename__ = "user_xp"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # XP and Level System
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    current_level_xp = Column(Integer, default=0)  # XP in current level
    next_level_xp = Column(Integer, default=1000)  # XP needed for next level
    
    # Currency System
    coins = Column(Integer, default=0)  # Spendable currency
    total_coins_earned = Column(Integer, default=0)  # Lifetime earnings
    total_coins_spent = Column(Integer, default=0)  # Lifetime spending
    
    # Badges and Achievements
    badges = Column(JSON, default=list)  # List of earned badge IDs/names
    achievements = Column(JSON, default=list)  # Achievement tracking
    
    # Stats
    lessons_completed = Column(Integer, default=0)
    quizzes_passed = Column(Integer, default=0)
    simulations_completed = Column(Integer, default=0)
    total_study_time_minutes = Column(Integer, default=0)
    
    # Streaks
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="xp_profile")
    transactions = relationship("XPTransaction", back_populates="user_xp", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserXP(user_id={self.user_id}, level={self.level}, xp={self.total_xp}, coins={self.coins})>"
    
    @property
    def level_progress_percentage(self):
        """Calculate percentage progress to next level"""
        if self.next_level_xp == 0:
            return 100
        return (self.current_level_xp / self.next_level_xp) * 100


class XPTransaction(Base):
    """
    Log of all XP and coin transactions for tracking and analytics
    """
    __tablename__ = "xp_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_xp_id = Column(Integer, ForeignKey("user_xp.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # "lesson_complete", "quiz_pass", "purchase", etc.
    xp_change = Column(Integer, default=0)  # Can be negative for penalties
    coin_change = Column(Integer, default=0)  # Can be negative for purchases
    
    # Reference to source
    source_type = Column(String(50), nullable=True)  # "lesson", "quiz", "boss_battle", "daily_run"
    source_id = Column(Integer, nullable=True)  # ID of the source
    
    # Description
    description = Column(String(500))
    
    # Metadata
    transaction_metadata = Column(JSON, nullable=True)  # Additional context    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user_xp = relationship("UserXP", back_populates="transactions")
    
    def __repr__(self):
        return f"<XPTransaction(id={self.id}, xp={self.xp_change}, coins={self.coin_change})>"