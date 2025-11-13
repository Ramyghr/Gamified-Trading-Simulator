from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime, date
import math

from app.models.user_xp import UserXP, XPTransaction
from app.schemas.lesson import RewardResponse


class XPService:
    """Service for managing user XP, levels, and coins"""
    
    # XP Level Calculation Constants - FIXED FOR BETTER BALANCE
    BASE_XP = 500  # Reduced from 700 - XP needed for level 2
    XP_MULTIPLIER = 1.15  # Reduced from 1.20 - Gentler progression (15% growth instead of 20%)
    
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
        
        # Add XP to total
        user_xp.total_xp += xp
        
        # Add coins
        user_xp.coins += coins
        user_xp.total_coins_earned += coins
        
        # Add badge if provided
        if badge and badge not in user_xp.badges:
            badges = user_xp.badges or []
            badges.append(badge)
            user_xp.badges = badges
        
        # FIXED: Recalculate level from total XP
        new_level, current_level_xp, next_level_xp = XPService.calculate_level_from_xp(user_xp.total_xp)
        
        # Update level fields
        level_up = new_level > old_level
        user_xp.level = new_level
        user_xp.current_level_xp = current_level_xp
        user_xp.next_level_xp = next_level_xp
        
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
        
        return user_xp, level_up, new_level if level_up else None
    
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
    def recalculate_user_level(db: Session, user_id: int) -> UserXP:
        """
        Recalculate user level from total XP (useful for fixing existing data)
        """
        user_xp = XPService.get_or_create_user_xp(db, user_id)
        
        # Recalculate from total XP
        new_level, current_level_xp, next_level_xp = XPService.calculate_level_from_xp(user_xp.total_xp)
        
        user_xp.level = new_level
        user_xp.current_level_xp = current_level_xp
        user_xp.next_level_xp = next_level_xp
        
        db.commit()
        db.refresh(user_xp)
        
        return user_xp
    
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


# =============================================================================
# UTILITY FUNCTIONS FOR XP MANAGEMENT
# =============================================================================

def print_xp_progression_table(max_level: int = 20):
    """Print XP requirements for each level (for testing/debugging)"""
    print("\n=== XP PROGRESSION TABLE ===")
    print(f"BASE_XP: {XPService.BASE_XP}, MULTIPLIER: {XPService.XP_MULTIPLIER}")
    print("-" * 60)
    print(f"{'Level':<8} {'XP Needed':<12} {'Total XP':<12} {'Lessons (~100XP)':<20}")
    print("-" * 60)
    
    total_xp = 0
    for level in range(1, max_level + 1):
        xp_needed = XPService.calculate_xp_for_level(level)
        total_xp += xp_needed
        lessons = xp_needed // 100 if xp_needed > 0 else 0
        
        print(f"{level:<8} {xp_needed:<12} {total_xp:<12} {lessons:<20}")
    print("-" * 60)


def recalculate_all_user_levels(db: Session):
    """
    Recalculate levels for ALL users (run this after changing XP constants)
    USE WITH CAUTION - Only run during maintenance
    """
    from app.models.user_xp import UserXP
    
    users = db.query(UserXP).all()
    updated_count = 0
    
    for user_xp in users:
        old_level = user_xp.level
        
        # Recalculate from total XP
        new_level, current_level_xp, next_level_xp = XPService.calculate_level_from_xp(user_xp.total_xp)
        
        if new_level != old_level:
            user_xp.level = new_level
            user_xp.current_level_xp = current_level_xp
            user_xp.next_level_xp = next_level_xp
            updated_count += 1
            print(f"User {user_xp.user_id}: Level {old_level} -> {new_level} (XP: {user_xp.total_xp})")
    
    db.commit()
    print(f"\nUpdated {updated_count} users")
    return updated_count


# =============================================================================
# XP PROGRESSION TABLE - With new balanced values
# =============================================================================
# Level 1->2: 500 XP (5 lessons @ 100 XP each)
# Level 2->3: 575 XP (4-5 lessons)
# Level 3->4: 661 XP (5-6 lessons)
# Level 4->5: 760 XP (6-7 lessons)
# Level 5->6: 874 XP (7-8 lessons)
# Level 6->7: 1005 XP (8-9 lessons)
# Level 7->8: 1156 XP (9-10 lessons)
# Level 8->9: 1329 XP (10-12 lessons)
# Level 9->10: 1528 XP (12-14 lessons)
# Level 10->11: 1758 XP (14-16 lessons)
#
# This gives a much smoother progression curve where users can level up
# approximately every chapter (5-7 lessons per chapter)
# =============================================================================