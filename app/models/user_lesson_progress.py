from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base


class UserLessonProgress(Base):
    """
    Tracks user progress through lessons
    """
    __tablename__ = "user_lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Completion status
    completed = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    
    # Rewards earned
    xp_earned = Column(Integer, default=0)
    coins_earned = Column(Integer, default=0)
    badge_earned = Column(String(100), nullable=True)
    
    # Type-specific tracking
    # For quizzes
    quiz_score = Column(Integer, nullable=True)  # Percentage or points
    quiz_answers = Column(JSON, nullable=True)  # Store user's answers
    
    # For videos
    watched_percentage = Column(Float, default=0.0)  # 0-100
    last_watched_position = Column(Integer, default=0)  # Seconds
    
    # For simulations
    simulation_result = Column(JSON, nullable=True)  # Trades, P&L, metrics
    simulation_score = Column(Float, nullable=True)  # Performance score
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="lesson_progress")
    lesson = relationship("Lesson", back_populates="user_progress")
    
    def __repr__(self):
        return f"<UserLessonProgress(user_id={self.user_id}, lesson_id={self.lesson_id}, completed={self.completed})>"