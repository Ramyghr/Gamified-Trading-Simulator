"""
Script to create chat tables in the database
Run this once to set up the chat functionality
"""
from sqlalchemy import create_engine
from app.config.database import SessionLocal, engine
from app.models.base import Base
from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User

db = SessionLocal()

def create_chat_tables():
    """Create chat-related tables"""
    
    
    print("Creating chat tables...")
    
    # Create only chat tables
    ChatConversation.__table__.create(bind=engine, checkfirst=True)
    ChatMessage.__table__.create(bind=engine, checkfirst=True)
    
    print("✅ Chat tables created successfully!")
    print("Tables created:")
    print("- chat_conversations")
    print("- chat_messages")

if __name__ == "__main__":
    create_chat_tables()