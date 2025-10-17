from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import math
from datetime import datetime, timedelta
from app.config.database import get_db
from app.models.user import User
from app.middleware.jwt_middleware import get_current_user
from app.schemas.lesson import (
    LessonCreate, LessonUpdate, LessonResponse, LessonListResponse,
    LessonWithProgress, LessonProgressResponse, LessonCompleteRequest,
    QuizCompleteRequest, SimulationCompleteRequest, LessonCompleteResponse,
    VideoProgressUpdate, XPStatusResponse, XPTransactionResponse,
    QuizQuestionCreate, QuizQuestionResponse, QuizQuestionPublic
)
from app.services.lesson_service import LessonService
from app.services.xp_service import XPService


router = APIRouter(prefix="/lessons", tags=["Lessons & Learning"])


# ============= Lesson CRUD =============

@router.post("/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lesson (Admin only)"""
    # TODO: Add admin role check
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    lesson = LessonService.create_lesson(db, lesson_data)
    return lesson


@router.get("/", response_model=LessonListResponse)
async def list_lessons(
    chapter: Optional[int] = Query(None, description="Filter by chapter"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    lesson_type: Optional[str] = Query(None, description="Filter by lesson type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all lessons with user progress"""
    lessons_with_progress, total = LessonService.get_lessons_with_progress(
        db=db,
        user_id=current_user.id,
        chapter=chapter,
        page=page,
        page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size)
    
    return {
        "lessons": lessons_with_progress,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific lesson"""
    lesson = LessonService.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check access
    can_access, reason = LessonService.check_lesson_access(db, current_user.id, lesson_id)
    if not can_access:
        raise HTTPException(status_code=403, detail=reason)
    
    return lesson


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a lesson (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    lesson = LessonService.update_lesson(db, lesson_id, lesson_data)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a lesson (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = LessonService.delete_lesson(db, lesson_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return None


# ============= Quiz Questions =============

@router.post("/{lesson_id}/questions", response_model=QuizQuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_quiz_question(
    lesson_id: int,
    question_data: QuizQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a quiz question to a lesson (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from app.models.lesson import LessonQuizQuestion
    
    lesson = LessonService.get_lesson(db, lesson_id)
    if not lesson or lesson.type != "quiz":
        raise HTTPException(status_code=400, detail="Invalid lesson or not a quiz")
    
    question = LessonQuizQuestion(**question_data.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return question


@router.get("/{lesson_id}/questions", response_model=List[QuizQuestionPublic])
async def get_quiz_questions(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quiz questions for a lesson (without correct answers)"""
    from app.models.lesson import LessonQuizQuestion
    
    # Check access
    can_access, reason = LessonService.check_lesson_access(db, current_user.id, lesson_id)
    if not can_access:
        raise HTTPException(status_code=403, detail=reason)
    
    lesson = LessonService.get_lesson(db, lesson_id)
    if not lesson or lesson.type != "quiz":
        raise HTTPException(status_code=400, detail="Lesson is not a quiz")
    
    questions = db.query(LessonQuizQuestion).filter(
        LessonQuizQuestion.lesson_id == lesson_id
    ).order_by(LessonQuizQuestion.order).all()
    
    # Return without correct answers
    return [
        QuizQuestionPublic(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            points=q.points,
            order=q.order
        )
        for q in questions
    ]


# ============= Lesson Completion =============

@router.post("/{lesson_id}/complete", response_model=LessonCompleteResponse)
async def complete_lesson(
    lesson_id: int,
    request: LessonCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete a generic lesson (video, reading)"""
    try:
        progress, rewards = LessonService.complete_lesson(
            db=db,
            user_id=current_user.id,
            lesson_id=lesson_id
        )
        
        return LessonCompleteResponse(
            success=True,
            message="Lesson completed successfully!",
            rewards=rewards,
            progress=progress
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lesson_id}/submit-quiz", response_model=LessonCompleteResponse)
async def submit_quiz(
    lesson_id: int,
    submission: QuizCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit quiz answers"""
    try:
        progress, rewards, quiz_results = LessonService.submit_quiz(
            db=db,
            user_id=current_user.id,
            lesson_id=lesson_id,
            submission=submission.answers
        )
        
        return LessonCompleteResponse(
            success=quiz_results["passed"],
            message=f"Quiz {'passed' if quiz_results['passed'] else 'failed'}! Score: {quiz_results['score']}%",
            rewards=rewards,
            progress=progress,
            quiz_results=quiz_results
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lesson_id}/submit-simulation", response_model=LessonCompleteResponse)
async def submit_simulation(
    lesson_id: int,
    submission: SimulationCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit simulation results"""
    try:
        progress, rewards = LessonService.submit_simulation(
            db=db,
            user_id=current_user.id,
            lesson_id=lesson_id,
            result=submission.result
        )
        
        return LessonCompleteResponse(
            success=progress.completed,
            message=f"Simulation {'completed' if progress.completed else 'attempted'}! Score: {progress.simulation_score:.1f}",
            rewards=rewards,
            progress=progress
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lesson_id}/video-progress")
async def update_video_progress(
    lesson_id: int,
    progress_data: VideoProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update video watching progress"""
    try:
        progress = LessonService.update_video_progress(
            db=db,
            user_id=current_user.id,
            lesson_id=lesson_id,
            progress_data=progress_data
        )
        return {"message": "Progress updated", "progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= Progress Tracking =============

@router.get("/{lesson_id}/progress", response_model=LessonProgressResponse)
async def get_lesson_progress(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's progress on a specific lesson"""
    progress = LessonService.get_user_progress(db, current_user.id, lesson_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for this lesson")
    
    return progress


# ============= XP & Gamification =============

@router.get("/xp/status", response_model=XPStatusResponse)
async def get_xp_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's XP, level, coins, and badges"""
    user_xp = XPService.get_user_xp_status(db, current_user.id)
    
    return XPStatusResponse(
        user_id=user_xp.user_id,
        level=user_xp.level,
        total_xp=user_xp.total_xp,
        current_level_xp=user_xp.current_level_xp,
        next_level_xp=user_xp.next_level_xp,
        level_progress_percentage=user_xp.level_progress_percentage,
        coins=user_xp.coins,
        total_coins_earned=user_xp.total_coins_earned,
        badges=user_xp.badges or [],
        lessons_completed=user_xp.lessons_completed,
        quizzes_passed=user_xp.quizzes_passed,
        simulations_completed=user_xp.simulations_completed,
        current_streak_days=user_xp.current_streak_days,
        longest_streak_days=user_xp.longest_streak_days
    )


@router.get("/xp/transactions", response_model=List[XPTransactionResponse])
async def get_xp_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's XP transaction history"""
    transactions = XPService.get_transaction_history(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    return transactions


# ============= Dashboard & Statistics =============

@router.get("/dashboard/stats")
async def get_learning_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive learning dashboard statistics"""
    from app.models.user_lesson_progress import UserLessonProgress
    
    user_xp = XPService.get_user_xp_status(db, current_user.id)
    
    # Get progress stats
    total_progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == current_user.id
    ).all()
    
    completed_lessons = [p for p in total_progress if p.completed]
    in_progress = [p for p in total_progress if not p.completed and p.watched_percentage and p.watched_percentage > 0]
    
    # Calculate average quiz score
    quiz_scores = [p.quiz_score for p in completed_lessons if p.quiz_score is not None]
    avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
    
    # Get next lessons to unlock
    from app.models.lesson import Lesson
    next_level_lessons = db.query(Lesson).filter(
        Lesson.required_level == user_xp.level + 1,
        Lesson.is_published == True,
        Lesson.is_active == True
    ).limit(3).all()
    
    return {
        "xp_status": {
            "level": user_xp.level,
            "total_xp": user_xp.total_xp,
            "level_progress": user_xp.level_progress_percentage,
            "coins": user_xp.coins,
            "badges": len(user_xp.badges or [])
        },
        "learning_stats": {
            "lessons_completed": len(completed_lessons),
            "lessons_in_progress": len(in_progress),
            "quizzes_passed": user_xp.quizzes_passed,
            "simulations_completed": user_xp.simulations_completed,
            "total_study_time_minutes": user_xp.total_study_time_minutes,
            "average_quiz_score": round(avg_quiz_score, 1)
        },
        "streaks": {
            "current_streak": user_xp.current_streak_days,
            "longest_streak": user_xp.longest_streak_days
        },
        "next_unlocks": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "type": lesson.type,
                "required_level": lesson.required_level
            }
            for lesson in next_level_lessons
        ]
    }


@router.get("/chapters")
async def get_chapters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chapters with completion status"""
    from app.models.lesson import Lesson
    from app.models.user_lesson_progress import UserLessonProgress
    from sqlalchemy import func, distinct
    
    # Get all chapters
    chapters = db.query(
        Lesson.chapter,
        func.count(Lesson.id).label('total_lessons')
    ).filter(
        Lesson.is_published == True,
        Lesson.is_active == True
    ).group_by(Lesson.chapter).order_by(Lesson.chapter).all()
    
    result = []
    for chapter_num, total in chapters:
        # Get completed lessons in this chapter
        completed = db.query(func.count(distinct(UserLessonProgress.lesson_id))).join(
            Lesson, Lesson.id == UserLessonProgress.lesson_id
        ).filter(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.completed == True,
            Lesson.chapter == chapter_num
        ).scalar() or 0
        
        result.append({
            "chapter": chapter_num,
            "total_lessons": total,
            "completed_lessons": completed,
            "completion_percentage": round((completed / total) * 100, 1) if total > 0 else 0
        })
    
    return {"chapters": result}


# ============= Leaderboard =============

@router.get("/leaderboard")
async def get_leaderboard(
    period: str = Query("all_time", regex="^(all_time|monthly|weekly)$"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get XP leaderboard"""
    from app.models.user_xp import UserXP
    from app.models.user import User
    from datetime import datetime, timedelta
    
    query = db.query(UserXP, User).join(User, User.id == UserXP.user_id)
    
    # Filter by period if needed
    if period == "weekly":
        week_ago = datetime.utcnow() - timedelta(days=7)
        # Would need a created_at on transactions to filter properly
        # For now, just show all-time
        pass
    elif period == "monthly":
        month_ago = datetime.utcnow() - timedelta(days=30)
        pass
    
    # Order by level and XP
    leaderboard = query.order_by(
        UserXP.level.desc(),
        UserXP.total_xp.desc()
    ).limit(limit).all()
    
    result = []
    for rank, (user_xp, user) in enumerate(leaderboard, start=1):
        result.append({
            "rank": rank,
            "user_id": user.id,
            "username": user.username,
            "level": user_xp.level,
            "total_xp": user_xp.total_xp,
            "lessons_completed": user_xp.lessons_completed,
            "badges": len(user_xp.badges or [])
        })
    
    # Find current user's rank
    user_rank = next((r for r in result if r["user_id"] == current_user.id), None)
    
    return {
        "leaderboard": result,
        "user_rank": user_rank,
        "period": period
    }