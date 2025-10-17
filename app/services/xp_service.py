from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime, date
import math

from app.models.user_xp import UserXP, XPTransaction
from app.schemas.lesson import RewardResponse


class XPService:
    """Service for managing user XP, levels, and coins"""
    
    # XP Level Calculation Constants
    BASE_XP = 1000  # XP needed for level 2
    XP_MULTIPLIER = 1.15  # XP requirement grows by 15% per level
    
    @staticmethod
    def calculate_xp_for_level(level: int) -> int:
        """Calculate XP required to reach a specific level"""
        if level <= 1:
            return 0
        return int(XPService.BASE_XP * math.pow(XPService.XP_MULTIPLIER, level - 2))
    
    @staticmethod
    def calculate_level_from_xp(total_xp: int) -> Tuple[int, int, int]:
        """
        Calculate level from total XP
        Returns: (level, current_level_xp, next_level_xp)
        """
        level = 1
        xp_accumulated = 0
        
        while True:
            xp_for_next = XPService.calculate_xp_for_level(level + 1)
            if xp_accumulated + xp_for_next > total_xp:
                # Current level found
                current_level_xp = total_xp - xp_accumulated
                return level, current_level_xp, xp_for_next
            
            xp_accumulated += xp_for_next
            level += 1
            
            # Safety cap at level 100
            if level >= 100:
                return 100, 0, 0
    
    @staticmethod
    def get_or_create_user_xp(db: Session, user_id: int) -> UserXP:
        """Get or create UserXP profile"""
        user_xp = db.query(UserXP).filter(UserXP.user_id == user_id).first()
        
        if not user_xp:
            user_xp = UserXP(
                user_id=user_id,
                total_xp=0,
                level=1,
                current_level_xp=0,
                next_level_xp=XPService.calculate_xp_for_level(2),
                coins=0
            )
            db.add(user_xp)
            db.commit()
            db.refresh(user_xp)
        
        return user_xp
    
    @staticmethod
    def award_xp(
        db: Session,
        user_id: int,
        xp: int,
        coins: int = 0,
        badge: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        description: str = "XP and coins earned"
    ) -> Tuple[UserXP, bool, Optional[int]]:
        """
        Award XP and coins to user
        Returns: (user_xp, level_up_occurred, new_level)
        """
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        
        # Track old level
        old_level = user_xp.level
        
        # Add XP
        user_xp.total_xp += xp
        user_xp.current_level_xp += xp
        
        # Add coins
        user_xp.coins += coins
        user_xp.total_coins_earned += coins
        
        # Add badge if provided
        if badge and badge not in user_xp.badges:
            badges = user_xp.badges or []
            badges.append(badge)
            user_xp.badges = badges
        
        # Check for level up
        level_up = False
        new_level = None
        
        while user_xp.current_level_xp >= user_xp.next_level_xp:
            user_xp.current_level_xp -= user_xp.next_level_xp
            user_xp.level += 1
            level_up = True
            new_level = user_xp.level
            user_xp.next_level_xp = XPService.calculate_xp_for_level(user_xp.level + 1)
        
        # Update activity tracking
        user_xp.last_activity_date = datetime.utcnow()
        XPService._update_streak(user_xp)
        
        # Create transaction record
        transaction = XPTransaction(
            user_xp_id=user_xp.id,
            transaction_type=source_type or "manual",
            xp_change=xp,
            coin_change=coins,
            source_type=source_type,
            source_id=source_id,
            description=description
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(user_xp)
        
        return user_xp, level_up, new_level
    
    @staticmethod
    def spend_coins(
        db: Session,
        user_id: int,
        amount: int,
        description: str = "Coins spent",
        source_type: Optional[str] = None
    ) -> bool:
        """
        Spend coins
        Returns: True if successful, False if insufficient funds
        """
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        
        if user_xp.coins < amount:
            return False
        
        user_xp.coins -= amount
        user_xp.total_coins_spent += amount
        
        # Create transaction record
        transaction = XPTransaction(
            user_xp_id=user_xp.id,
            transaction_type=source_type or "purchase",
            xp_change=0,
            coin_change=-amount,
            source_type=source_type,
            description=description
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(user_xp)
        
        return True
    
    @staticmethod
    def _update_streak(user_xp: UserXP):
        """Update daily streak tracking"""
        today = date.today()
        
        if user_xp.last_activity_date:
            last_date = user_xp.last_activity_date.date()
            days_diff = (today - last_date).days
            
            if days_diff == 0:
                # Same day, no change
                pass
            elif days_diff == 1:
                # Consecutive day, increment streak
                user_xp.current_streak_days += 1
                if user_xp.current_streak_days > user_xp.longest_streak_days:
                    user_xp.longest_streak_days = user_xp.current_streak_days
            else:
                # Streak broken
                user_xp.current_streak_days = 1
        else:
            # First activity
            user_xp.current_streak_days = 1
            user_xp.longest_streak_days = 1
    
    @staticmethod
    def get_user_xp_status(db: Session, user_id: int) -> UserXP:
        """Get user's XP status"""
        return XPService.get_or_create_user_xp(db, user_id)
    
    @staticmethod
    def get_transaction_history(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[XPTransaction]:
        """Get user's XP transaction history"""
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        
        transactions = db.query(XPTransaction)\
            .filter(XPTransaction.user_xp_id == user_xp.id)\
            .order_by(XPTransaction.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return transactions
    
    @staticmethod
    def increment_lesson_stats(db: Session, user_id: int, stat_type: str):
        """Increment lesson-related statistics"""
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        
        if stat_type == "lesson":
            user_xp.lessons_completed += 1
        elif stat_type == "quiz":
            user_xp.quizzes_passed += 1
        elif stat_type == "simulation":
            user_xp.simulations_completed += 1
        
        db.commit()
    
    @staticmethod
    def add_study_time(db: Session, user_id: int, minutes: int):
        """Add study time to user stats"""
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        user_xp.total_study_time_minutes += minutes
        db.commit()