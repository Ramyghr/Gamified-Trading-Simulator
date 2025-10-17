from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.models.lesson import Lesson, LessonQuizQuestion
from app.models.user_lesson_progress import UserLessonProgress
from app.models.user_xp import UserXP
from app.schemas.lesson import (
    LessonCreate, LessonUpdate, QuizSubmission, SimulationResult,
    VideoProgressUpdate, RewardResponse, LessonWithProgress
)
from app.services.xp_service import XPService


class LessonService:
    """Service for managing lessons and user progress"""
    
    @staticmethod
    def create_lesson(db: Session, lesson_data: LessonCreate) -> Lesson:
        """Create a new lesson"""
        lesson = Lesson(**lesson_data.model_dump())
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson
    
    @staticmethod
    def get_lesson(db: Session, lesson_id: int) -> Optional[Lesson]:
        """Get lesson by ID"""
        return db.query(Lesson).filter(
            Lesson.id == lesson_id,
            Lesson.is_active == True
        ).first()
    
    @staticmethod
    def list_lessons(
        db: Session,
        chapter: Optional[int] = None,
        difficulty: Optional[str] = None,
        lesson_type: Optional[str] = None,
        user_id: Optional[int] = None,
        published_only: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Lesson], int]:
        """List lessons with optional filters"""
        query = db.query(Lesson).filter(Lesson.is_active == True)
        
        if published_only:
            query = query.filter(Lesson.is_published == True)
        
        if chapter is not None:
            query = query.filter(Lesson.chapter == chapter)
        
        if difficulty:
            query = query.filter(Lesson.difficulty == difficulty)
        
        if lesson_type:
            query = query.filter(Lesson.type == lesson_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        lessons = query.order_by(Lesson.chapter, Lesson.order)\
            .limit(page_size)\
            .offset((page - 1) * page_size)\
            .all()
        
        return lessons, total
    
    @staticmethod
    def update_lesson(db: Session, lesson_id: int, lesson_data: LessonUpdate) -> Lesson:
        """Update a lesson"""
        lesson = LessonService.get_lesson(db, lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        update_data = lesson_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(lesson, key, value)
        
        db.commit()
        db.refresh(lesson)
        return lesson
    
    @staticmethod
    def delete_lesson(db: Session, lesson_id: int) -> bool:
        """Soft delete a lesson"""
        lesson = LessonService.get_lesson(db, lesson_id)
        if not lesson:
            return False
        
        lesson.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def check_lesson_access(db: Session, user_id: int, lesson_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user can access a lesson
        Returns: (can_access, lock_reason)
        """
        lesson = LessonService.get_lesson(db, lesson_id)
        if not lesson:
            return False, "Lesson not found"
        
        # Check if published
        if not lesson.is_published:
            return False, "Lesson not published"
        
        # Check user level requirement
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        if user_xp.level < lesson.required_level:
            return False, f"Requires level {lesson.required_level}"
        
        # Check prerequisite
        if lesson.prerequisite_lesson_id:
            prereq_progress = db.query(UserLessonProgress).filter(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == lesson.prerequisite_lesson_id,
                UserLessonProgress.completed == True
            ).first()
            
            if not prereq_progress:
                return False, "Complete prerequisite lesson first"
        
        return True, None
    
    @staticmethod
    def get_or_create_progress(db: Session, user_id: int, lesson_id: int) -> UserLessonProgress:
        """Get or create user lesson progress"""
        progress = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()
        
        if not progress:
            progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
        
        return progress
    
    @staticmethod
    def complete_lesson(
        db: Session,
        user_id: int,
        lesson_id: int
    ) -> Tuple[UserLessonProgress, RewardResponse]:
        """
        Complete a generic lesson (video, reading)
        """
        # Check access
        can_access, reason = LessonService.check_lesson_access(db, user_id, lesson_id)
        if not can_access:
            raise HTTPException(status_code=403, detail=reason)
        
        lesson = LessonService.get_lesson(db, lesson_id)
        progress = LessonService.get_or_create_progress(db, user_id, lesson_id)
        
        # Mark as completed
        if not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            progress.attempts += 1
            
            # Award XP and coins
            user_xp, level_up, new_level = XPService.award_xp(
                db=db,
                user_id=user_id,
                xp=lesson.xp_reward,
                coins=lesson.coin_reward,
                badge=lesson.badge_reward,
                source_type="lesson",
                source_id=lesson_id,
                description=f"Completed lesson: {lesson.title}"
            )
            
            progress.xp_earned = lesson.xp_reward
            progress.coins_earned = lesson.coin_reward
            progress.badge_earned = lesson.badge_reward
            
            # Update stats
            XPService.increment_lesson_stats(db, user_id, "lesson")
            XPService.add_study_time(db, user_id, lesson.duration_minutes)
            
            # Check for unlocked lessons
            unlocked = LessonService._check_unlocked_lessons(db, user_id, new_level if level_up else None)
            
            db.commit()
            db.refresh(progress)
            
            rewards = RewardResponse(
                xp_gained=lesson.xp_reward,
                coins_gained=lesson.coin_reward,
                badge_earned=lesson.badge_reward,
                level_up=level_up,
                new_level=new_level,
                unlocked_lessons=unlocked
            )
        else:
            # Already completed
            rewards = RewardResponse(
                xp_gained=0,
                coins_gained=0,
                level_up=False,
                unlocked_lessons=[]
            )
        
        return progress, rewards
    
    @staticmethod
    def submit_quiz(
        db: Session,
        user_id: int,
        lesson_id: int,
        submission: QuizSubmission
    ) -> Tuple[UserLessonProgress, RewardResponse, Dict[str, Any]]:
        """
        Submit quiz answers and calculate score
        """
        from datetime import datetime
        
        # Check access
        can_access, reason = LessonService.check_lesson_access(db, user_id, lesson_id)
        if not can_access:
            raise HTTPException(status_code=403, detail=reason)
        
        lesson = LessonService.get_lesson(db, lesson_id)
        if lesson.type != "quiz":
            raise HTTPException(status_code=400, detail="Lesson is not a quiz")
        
        # Get quiz questions
        questions = db.query(LessonQuizQuestion).filter(
            LessonQuizQuestion.lesson_id == lesson_id
        ).all()
        
        if not questions:
            raise HTTPException(status_code=400, detail="No questions found for this quiz")
        
        # Evaluate answers
        total_points = sum(q.points for q in questions)
        earned_points = 0
        results = []
        
        answer_dict = {ans.question_id: ans.answer for ans in submission.answers}
        
        for question in questions:
            user_answer = answer_dict.get(question.id, "")
            is_correct = user_answer.upper() == question.correct_answer.upper()
            
            if is_correct:
                earned_points += question.points
            
            results.append({
                "question_id": question.id,
                "question": question.question_text,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "points_earned": question.points if is_correct else 0
            })
        
        # Calculate percentage
        percentage_score = int((earned_points / total_points) * 100) if total_points > 0 else 0
        passing_score = 70  # 70% to pass
        passed = percentage_score >= passing_score
        
        # Update progress
        progress = LessonService.get_or_create_progress(db, user_id, lesson_id)
        progress.attempts += 1
        progress.quiz_score = percentage_score
        progress.quiz_answers = answer_dict
        
        # Award rewards if passed and not completed before
        if passed and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            
            # Award XP and coins
            user_xp, level_up, new_level = XPService.award_xp(
                db=db,
                user_id=user_id,
                xp=lesson.xp_reward,
                coins=lesson.coin_reward,
                badge=lesson.badge_reward,
                source_type="quiz",
                source_id=lesson_id,
                description=f"Passed quiz: {lesson.title} ({percentage_score}%)"
            )
            
            progress.xp_earned = lesson.xp_reward
            progress.coins_earned = lesson.coin_reward
            progress.badge_earned = lesson.badge_reward
            
            # Update stats
            XPService.increment_lesson_stats(db, user_id, "quiz")
            XPService.add_study_time(db, user_id, lesson.duration_minutes)
            
            # Check for unlocked lessons
            unlocked = LessonService._check_unlocked_lessons(db, user_id, new_level if level_up else None)
            
            db.commit()
            db.refresh(progress)
            
            rewards = RewardResponse(
                xp_gained=lesson.xp_reward,
                coins_gained=lesson.coin_reward,
                badge_earned=lesson.badge_reward,
                level_up=level_up,
                new_level=new_level,
                unlocked_lessons=unlocked
            )
        else:
            rewards = RewardResponse(
                xp_gained=0,
                coins_gained=0,
                level_up=False,
                unlocked_lessons=[]
            )
        
        quiz_results = {
            "passed": passed,
            "score": percentage_score,
            "passing_score": passing_score,
            "total_points": total_points,
            "earned_points": earned_points,
            "results": results
        }
        
        db.commit()
        db.refresh(progress)
        
        return progress, rewards, quiz_results
    
    @staticmethod
    def submit_simulation(
        db: Session,
        user_id: int,
        lesson_id: int,
        result: SimulationResult
    ) -> Tuple[UserLessonProgress, RewardResponse]:
        """
        Submit simulation results and evaluate performance
        """
        from datetime import datetime
        
        # Check access
        can_access, reason = LessonService.check_lesson_access(db, user_id, lesson_id)
        if not can_access:
            raise HTTPException(status_code=403, detail=reason)
        
        lesson = LessonService.get_lesson(db, lesson_id)
        if lesson.type not in ["simulation", "scenario"]:
            raise HTTPException(status_code=400, detail="Lesson is not a simulation")
        
        # Evaluate performance (simple scoring based on P&L and win rate)
        performance_score = LessonService._calculate_simulation_score(result)
        passing_score = 60.0
        passed = performance_score >= passing_score
        
        # Update progress
        progress = LessonService.get_or_create_progress(db, user_id, lesson_id)
        progress.attempts += 1
        progress.simulation_result = result.model_dump()
        progress.simulation_score = performance_score
        
        # Award rewards if passed and not completed before
        if passed and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            
            # Award XP and coins
            user_xp, level_up, new_level = XPService.award_xp(
                db=db,
                user_id=user_id,
                xp=lesson.xp_reward,
                coins=lesson.coin_reward,
                badge=lesson.badge_reward,
                source_type="simulation",
                source_id=lesson_id,
                description=f"Completed simulation: {lesson.title} (Score: {performance_score:.1f})"
            )
            
            progress.xp_earned = lesson.xp_reward
            progress.coins_earned = lesson.coin_reward
            progress.badge_earned = lesson.badge_reward
            
            # Update stats
            XPService.increment_lesson_stats(db, user_id, "simulation")
            XPService.add_study_time(db, user_id, lesson.duration_minutes)
            
            # Check for unlocked lessons
            unlocked = LessonService._check_unlocked_lessons(db, user_id, new_level if level_up else None)
            
            db.commit()
            db.refresh(progress)
            
            rewards = RewardResponse(
                xp_gained=lesson.xp_reward,
                coins_gained=lesson.coin_reward,
                badge_earned=lesson.badge_reward,
                level_up=level_up,
                new_level=new_level,
                unlocked_lessons=unlocked
            )
        else:
            rewards = RewardResponse(
                xp_gained=0,
                coins_gained=0,
                level_up=False,
                unlocked_lessons=[]
            )
        
        db.commit()
        db.refresh(progress)
        
        return progress, rewards
    
    @staticmethod
    def update_video_progress(
        db: Session,
        user_id: int,
        lesson_id: int,
        progress_data: VideoProgressUpdate
    ) -> UserLessonProgress:
        """Update video watching progress"""
        progress = LessonService.get_or_create_progress(db, user_id, lesson_id)
        
        progress.watched_percentage = progress_data.watched_percentage
        progress.last_watched_position = progress_data.last_position
        
        # Auto-complete if watched >= 90%
        if progress_data.watched_percentage >= 90 and not progress.completed:
            progress, _ = LessonService.complete_lesson(db, user_id, lesson_id)
        
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def get_user_progress(db: Session, user_id: int, lesson_id: int) -> Optional[UserLessonProgress]:
        """Get user's progress on a specific lesson"""
        return db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id
        ).first()
    
    @staticmethod
    def get_lessons_with_progress(
        db: Session,
        user_id: int,
        chapter: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LessonWithProgress], int]:
        """Get lessons with user progress info"""
        lessons, total = LessonService.list_lessons(
            db, chapter=chapter, user_id=user_id, page=page, page_size=page_size
        )
        
        # Get user's XP level
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        
        # Get all progress records for these lessons
        lesson_ids = [l.id for l in lessons]
        progress_records = db.query(UserLessonProgress).filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id.in_(lesson_ids)
        ).all()
        
        progress_map = {p.lesson_id: p for p in progress_records}
        
        # Build response with progress
        lessons_with_progress = []
        for lesson in lessons:
            can_access, lock_reason = LessonService.check_lesson_access(db, user_id, lesson.id)
            progress = progress_map.get(lesson.id)
            
            lesson_data = LessonWithProgress(
                **lesson.__dict__,
                user_completed=progress.completed if progress else False,
                user_progress=progress.watched_percentage if progress and progress.watched_percentage else None,
                is_locked=not can_access,
                lock_reason=lock_reason
            )
            lessons_with_progress.append(lesson_data)
        
        return lessons_with_progress, total
    
    @staticmethod
    def _calculate_simulation_score(result: SimulationResult) -> float:
        """
        Calculate performance score for simulation
        Score is based on: P&L%, win rate, and risk management
        """
        # P&L component (max 50 points)
        pl_score = min(50, max(0, result.profit_loss_percentage * 5))
        
        # Win rate component (max 30 points)
        win_rate_score = result.win_rate * 30
        
        # Risk management component (max 20 points)
        # Penalize too many trades or too few
        ideal_trades = 5
        trade_diff = abs(result.total_trades - ideal_trades)
        risk_score = max(0, 20 - (trade_diff * 2))
        
        total_score = pl_score + win_rate_score + risk_score
        return min(100, total_score)
    
    @staticmethod
    def _check_unlocked_lessons(
        db: Session,
        user_id: int,
        new_level: Optional[int] = None
    ) -> List[int]:
        """
        Check if any new lessons were unlocked
        Returns list of newly unlocked lesson IDs
        """
        if not new_level:
            return []
        
        # Find lessons that require this level and aren't completed yet
        unlocked = db.query(Lesson.id).filter(
            Lesson.required_level == new_level,
            Lesson.is_published == True,
            Lesson.is_active == True,
            ~Lesson.id.in_(
                db.query(UserLessonProgress.lesson_id).filter(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.completed == True
                )
            )
        ).all()
        
        return [lesson_id for (lesson_id,) in unlocked]