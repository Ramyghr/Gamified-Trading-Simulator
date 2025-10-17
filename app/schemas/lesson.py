from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LessonType(str, Enum):
    """Lesson type enumeration"""
    VIDEO = "video"
    QUIZ = "quiz"
    SIMULATION = "simulation"
    SCENARIO = "scenario"
    READING = "reading"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ============= Quiz Schemas =============

class QuizQuestionBase(BaseModel):
    question_text: str = Field(..., max_length=1000)
    question_type: str = Field(default="multiple_choice")
    options: Dict[str, str]
    correct_answer: str
    explanation: Optional[str] = None
    points: int = Field(default=10, ge=1)
    order: int = Field(default=0)


class QuizQuestionCreate(QuizQuestionBase):
    lesson_id: int


class QuizQuestionResponse(QuizQuestionBase):
    id: int
    lesson_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizQuestionPublic(BaseModel):
    """Public quiz question (without correct answer)"""
    id: int
    question_text: str
    question_type: str
    options: Dict[str, str]
    points: int
    order: int


class QuizAnswerSubmission(BaseModel):
    """User's quiz answer submission"""
    question_id: int
    answer: str


class QuizSubmission(BaseModel):
    """Complete quiz submission"""
    answers: List[QuizAnswerSubmission]


# ============= Lesson Schemas =============

class LessonBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    chapter: int = Field(..., ge=1)
    order: int = Field(..., ge=0)
    type: LessonType
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    content: Dict[str, Any]
    duration_minutes: int = Field(default=5, ge=1)
    xp_reward: int = Field(default=100, ge=0)
    coin_reward: int = Field(default=50, ge=0)
    badge_reward: Optional[str] = None
    prerequisite_lesson_id: Optional[int] = None
    required_level: int = Field(default=1, ge=1)
    tags: List[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None


class LessonCreate(LessonBase):
    is_published: bool = False


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    duration_minutes: Optional[int] = None
    xp_reward: Optional[int] = None
    coin_reward: Optional[int] = None
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None


class LessonResponse(LessonBase):
    id: int
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LessonWithProgress(LessonResponse):
    """Lesson with user progress info"""
    user_completed: bool = False
    user_progress: Optional[float] = None
    is_locked: bool = False
    lock_reason: Optional[str] = None


class LessonListResponse(BaseModel):
    """Paginated lesson list"""
    lessons: List[LessonWithProgress]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============= Progress Schemas =============

class VideoProgressUpdate(BaseModel):
    """Video watching progress"""
    watched_percentage: float = Field(..., ge=0, le=100)
    last_position: int = Field(..., ge=0)


class SimulationResult(BaseModel):
    """Simulation performance data"""
    trades: List[Dict[str, Any]]
    final_balance: float
    profit_loss: float
    profit_loss_percentage: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    metrics: Dict[str, Any] = {}


class LessonProgressResponse(BaseModel):
    """User's progress on a lesson"""
    id: int
    lesson_id: int
    completed: bool
    attempts: int
    xp_earned: int
    coins_earned: int
    badge_earned: Optional[str]
    quiz_score: Optional[int]
    watched_percentage: Optional[float]
    simulation_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= XP & Coins Schemas =============

class XPStatusResponse(BaseModel):
    """User's XP and gamification status"""
    user_id: int
    level: int
    total_xp: int
    current_level_xp: int
    next_level_xp: int
    level_progress_percentage: float
    coins: int
    total_coins_earned: int
    badges: List[str]
    lessons_completed: int
    quizzes_passed: int
    simulations_completed: int
    current_streak_days: int
    longest_streak_days: int
    
    class Config:
        from_attributes = True


class XPTransactionResponse(BaseModel):
    """XP/Coin transaction record"""
    id: int
    transaction_type: str
    xp_change: int
    coin_change: int
    description: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RewardResponse(BaseModel):
    """Reward given for completing an action"""
    xp_gained: int
    coins_gained: int
    badge_earned: Optional[str] = None
    level_up: bool = False
    new_level: Optional[int] = None
    unlocked_lessons: List[int] = Field(default_factory=list)


# ============= Completion Schemas =============

class LessonCompleteRequest(BaseModel):
    """Generic lesson completion (for videos, reading)"""
    pass


class QuizCompleteRequest(BaseModel):
    """Quiz completion with answers"""
    answers: List[QuizAnswerSubmission]


class SimulationCompleteRequest(BaseModel):
    """Simulation completion with results"""
    result: SimulationResult


class LessonCompleteResponse(BaseModel):
    """Response after completing a lesson"""
    success: bool
    message: str
    rewards: RewardResponse
    progress: LessonProgressResponse
    quiz_results: Optional[Dict[str, Any]] = None  # For quiz feedback