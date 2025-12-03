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
from app.services.xp_service import XPService
from app.models.user_xp import UserXP

router = APIRouter(prefix="/lessons", tags=["Lessons & Learning"])


# ============= XP & Gamification (MUST BE BEFORE /{lesson_id}) =============

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


# ============= Dashboard & Statistics (MUST BE BEFORE /{lesson_id}) =============

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


# ============= Leaderboard (MUST BE BEFORE /{lesson_id}) =============

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
            "username": user.display_name,
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


# ============= Lesson CRUD =============




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


# ============= THESE ROUTES MUST COME AFTER ALL SPECIFIC PATHS =============

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




# ============= Quiz Questions =============

@router.get("/{lesson_id}/questions", response_model=List[QuizQuestionPublic])
async def get_quiz_questions(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quiz questions for a lesson (without correct answers)"""
    from app.models.lesson import LessonQuizQuestion
    
    # Check access first
    can_access, reason = LessonService.check_lesson_access(db, current_user.id, lesson_id)
    if not can_access:
        raise HTTPException(status_code=403, detail=reason)
    
    lesson = LessonService.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Only allow quiz lessons to have questions
    if lesson.type != "quiz":
        raise HTTPException(
            status_code=400, 
            detail=f"Lesson is not a quiz (type: {lesson.type})"
        )
    
    questions = db.query(LessonQuizQuestion).filter(
        LessonQuizQuestion.lesson_id == lesson_id
    ).order_by(LessonQuizQuestion.order).all()
    
    # Handle case where no questions exist
    if not questions:
        return []
    
    # Convert to public format (without correct answers)
    result = []
    for q in questions:
        options = q.options if isinstance(q.options, list) else []
        
        result.append(
            QuizQuestionPublic(
                id=q.id,
                question_text=q.question_text,
                question_type=q.question_type or "multiple_choice",
                options=options,
                points=q.points if q.points is not None else 10,
                order=q.order
            )
        )
    
    return result


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
            submission=submission
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



@router.post("/recalculate-my-level")
async def recalculate_my_level(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recalculate current user's level (available to all users).
    Useful if you think your level is incorrect.
    """
    user_xp = XPService.get_or_create_user_xp(db, current_user.id)
    
    old_level = user_xp.level
    old_current = user_xp.current_level_xp
    old_next = user_xp.next_level_xp
    
    # Recalculate
    new_level, current_level_xp, next_level_xp = XPService.calculate_level_from_xp(user_xp.total_xp)
    
    user_xp.level = new_level
    user_xp.current_level_xp = current_level_xp
    user_xp.next_level_xp = next_level_xp
    
    db.commit()
    db.refresh(user_xp)
    
    return {
        "success": True,
        "message": "Level recalculated successfully",
        "changes": {
            "level_changed": old_level != new_level,
            "old_level": old_level,
            "new_level": new_level,
            "total_xp": user_xp.total_xp,
            "old_progress": f"{old_current}/{old_next}",
            "new_progress": f"{current_level_xp}/{next_level_xp}"
        },
        "current_status": {
            "level": user_xp.level,
            "total_xp": user_xp.total_xp,
            "current_level_xp": user_xp.current_level_xp,
            "next_level_xp": user_xp.next_level_xp,
            "progress_percentage": user_xp.level_progress_percentage
        }
    }


@router.get("/xp-progression-table")
async def get_xp_progression_table(
    max_level: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Get XP requirements for each level.
    Shows how much XP is needed to reach each level.
    """
    progression = []
    total_xp = 0
    
    for level in range(1, max_level + 1):
        xp_needed = XPService.calculate_xp_for_level(level)
        total_xp += xp_needed
        
        progression.append({
            "level": level,
            "xp_for_this_level": xp_needed,
            "total_xp_needed": total_xp,
            "approx_lessons_100xp": xp_needed // 100 if xp_needed > 0 else 0,
            "approx_lessons_150xp": xp_needed // 150 if xp_needed > 0 else 0
        })
    
    return {
        "base_xp": XPService.BASE_XP,
        "multiplier": XPService.XP_MULTIPLIER,
        "progression": progression
    }
    