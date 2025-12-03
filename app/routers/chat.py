from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatResponse, 
    ConversationResponse, 
    ConversationWithMessages,
    ConversationCreate
)
from app.services.llm.chat_service import chat_service
from app.middleware.jwt_middleware import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Financial Coach"])

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: str = Form(..., description="Your message to the financial coach"),
    conversation_id: Optional[int] = Form(None, description="Optional conversation ID to continue existing chat"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to the financial coach AI
    - Creates a new conversation if conversation_id is not provided or is None
    - conversation_id=0 will create a new conversation (treated as None)
    - Saves both user message and AI response to database
    - Returns conversation_id for future messages
    """
    try:
        # Treat 0 as None (new conversation)
        if conversation_id == 0:
            conversation_id = None
            
        result = await chat_service.chat_with_llm(
            db=db,
            user_id=current_user.id,
            message=message,
            conversation_id=conversation_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all chat conversations for the current user
    - Returns list sorted by most recent activity
    - Includes message count for each conversation
    """
    conversations = chat_service.get_user_conversations(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with all its messages
    """
    conversation = chat_service.get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": len(conversation.messages),
        "messages": conversation.messages
    }

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    title: str = Form("New Conversation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation manually
    """
    conversation = chat_service.create_conversation(
        db=db,
        user_id=current_user.id,
        title=title
    )
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": 0
    }

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages
    """
    success = chat_service.delete_conversation(db, conversation_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return {"message": "Conversation deleted successfully"}

@router.patch("/conversations/{conversation_id}/title")
def update_conversation_title(
    conversation_id: int,
    title: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update conversation title
    """
    conversation = chat_service.update_conversation_title(
        db, conversation_id, current_user.id, title
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return {"message": "Title updated successfully", "title": conversation.title}