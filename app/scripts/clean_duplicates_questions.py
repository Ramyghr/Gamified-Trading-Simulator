# scripts/cleanup_duplicate_questions.py
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config.database import SessionLocal
from app.models.lesson import LessonQuizQuestion


def cleanup_duplicate_questions():
    db = SessionLocal()
    try:
        # Find lessons with duplicate questions
        duplicates = db.execute("""
            SELECT lesson_id, question_text, COUNT(*) as count
            FROM lesson_quiz_questions 
            GROUP BY lesson_id, question_text 
            HAVING COUNT(*) > 1
        """).fetchall()
        
        print(f"Found {len(duplicates)} lessons with duplicate questions")
        
        for lesson_id, question_text, count in duplicates:
            print(f"Lesson {lesson_id}: '{question_text}' has {count} duplicates")
            
            # Keep the first occurrence, delete others
            questions = db.query(LessonQuizQuestion).filter(
                LessonQuizQuestion.lesson_id == lesson_id,
                LessonQuizQuestion.question_text == question_text
            ).order_by(LessonQuizQuestion.id).all()
            
            # Delete all but the first one
            for question in questions[1:]:
                print(f"Deleting duplicate question ID: {question.id}")
                db.delete(question)
            
            db.commit()
            
        print("Cleanup completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicate_questions()