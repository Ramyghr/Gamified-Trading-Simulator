from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base


class Lesson(Base):
    """
    Represents a learning lesson (video, quiz, simulation, scenario)
    """
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(1000))
    chapter = Column(Integer, nullable=False, index=True)  # Grouping lessons into chapters
    order = Column(Integer, nullable=False)  # Order within chapter
    type = Column(String(50), nullable=False)  # "video", "quiz", "simulation", "scenario"
    difficulty = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    
    # Content (varies by type)
    content = Column(JSON)  # URL for videos, questions for quizzes, scenario data for simulations
    duration_minutes = Column(Integer, default=5)
    
    # Rewards
    xp_reward = Column(Integer, default=100)
    coin_reward = Column(Integer, default=50)
    badge_reward = Column(String(100), nullable=True)  # Optional badge earned
    
    # Prerequisites and unlocking
    prerequisite_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    required_level = Column(Integer, default=1)  # User level required to access
    
    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    
    # Metadata
    tags = Column(JSON, default=list)  # ["stocks", "risk-management", "technical-analysis"]
    thumbnail_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prerequisite = relationship("Lesson", remote_side=[id], backref="unlocks")
    user_progress = relationship("UserLessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    quiz_questions = relationship("LessonQuizQuestion", back_populates="lesson", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title='{self.title}', type='{self.type}')>"


class LessonQuizQuestion(Base):
    """
    Questions for quiz-type lessons
    """
    __tablename__ = "lesson_quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(String(1000), nullable=False)
    question_type = Column(String(50), default="multiple_choice")  # multiple_choice, true_false, scenario
    
    # Options stored as JSON: {"A": "option1", "B": "option2", "C": "option3", "D": "option4"}
    options = Column(JSON, nullable=False)
    correct_answer = Column(String(10), nullable=False)  # "A", "B", "C", "D" or "true", "false"
    
    # Explanation shown after answering
    explanation = Column(String(1000), nullable=True)
    
    # Points awarded for correct answer
    points = Column(Integer, default=10)
    order = Column(Integer, default=0)  # Order in quiz
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quiz_questions")
    
    def __repr__(self):
        return f"<QuizQuestion(id={self.id}, lesson_id={self.lesson_id})>"