from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime

from app.models.chat import ChatConversation, ChatMessage, MessageRole
from app.models.portfolio import Portfolio
from app.services.llm.llm_service import llm_service

class ChatService:
    
    @staticmethod
    def create_conversation(db: Session, user_id: int, title: str = "New Conversation") -> ChatConversation:
        """Create a new chat conversation"""
        conversation = ChatConversation(
            user_id=user_id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: int, user_id: int) -> Optional[ChatConversation]:
        """Get a specific conversation for a user"""
        return db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user_id
        ).first()
    
    @staticmethod
    def get_user_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[Dict]:
        """Get all conversations for a user with message count"""
        conversations = db.query(
            ChatConversation,
            func.count(ChatMessage.id).label('message_count')
        ).outerjoin(
            ChatMessage, ChatConversation.id == ChatMessage.conversation_id
        ).filter(
            ChatConversation.user_id == user_id
        ).group_by(
            ChatConversation.id
        ).order_by(
            ChatConversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        result = []
        for conv, msg_count in conversations:
            conv_dict = {
                "id": conv.id,
                "user_id": conv.user_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": msg_count
            }
            result.append(conv_dict)
        
        return result
    
    @staticmethod
    def get_conversation_messages(db: Session, conversation_id: int, user_id: int) -> List[ChatMessage]:
        """Get all messages in a conversation"""
        conversation = ChatService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return []
        return conversation.messages
    
    @staticmethod
    def add_message(
        db: Session, 
        conversation_id: int, 
        role: MessageRole, 
        content: str
    ) -> ChatMessage:
        """Add a message to a conversation"""
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: int, user_id: int) -> bool:
        """Delete a conversation and all its messages"""
        conversation = ChatService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        
        db.delete(conversation)
        db.commit()
        return True
    
    @staticmethod
    def update_conversation_title(db: Session, conversation_id: int, user_id: int, title: str) -> Optional[ChatConversation]:
        """Update conversation title"""
        conversation = ChatService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return None
        
        conversation.title = title
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def get_user_context(db: Session, user_id: int) -> Dict:
        """Get user context for personalized responses"""
        context = {}
        
        try:
            # Get portfolio information - handle different Portfolio model structures
            portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
            if portfolio:
                # Try different attribute names based on your Portfolio model
                cash_balance = getattr(portfolio, 'cash_balance', None) or getattr(portfolio, 'balance', None) or 0
                
                # Calculate invested amount from positions if not directly available
                invested_amount = 0
                if hasattr(portfolio, 'invested_amount'):
                    invested_amount = float(portfolio.invested_amount)
                elif hasattr(portfolio, 'positions') and portfolio.positions:
                    # Calculate from positions if available
                    for position in portfolio.positions:
                        if hasattr(position, 'current_value'):
                            invested_amount += float(position.current_value)
                        elif hasattr(position, 'quantity') and hasattr(position, 'current_price'):
                            invested_amount += float(position.quantity * position.current_price)
                
                context["portfolio_value"] = float(cash_balance) + invested_amount
                context["cash_balance"] = float(cash_balance)
                context["invested_amount"] = invested_amount
                
                # Add total portfolio value if available
                if hasattr(portfolio, 'total_value'):
                    context["portfolio_value"] = float(portfolio.total_value)
                    
        except Exception as e:
            # If portfolio context fails, continue without it
            print(f"Warning: Could not fetch portfolio context: {str(e)}")
            pass
        
        # You can add more context here:
        # - User's XP level
        # - Trading history
        # - Risk profile
        # - Preferred trading style
        
        return context
    
    @staticmethod
    async def chat_with_llm(
        db: Session, 
        user_id: int, 
        message: str, 
        conversation_id: Optional[int] = None
    ) -> Dict:
        """Main chat function with LLM"""
        
        # Create new conversation if none provided or if conversation_id is None
        if conversation_id is None:
            conversation = ChatService.create_conversation(db, user_id)
            conversation_id = conversation.id
        else:
            # Verify conversation belongs to user
            conversation = ChatService.get_conversation(db, conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found or access denied")
        
        # Get conversation history
        messages = ChatService.get_conversation_messages(db, conversation_id, user_id)
        conversation_history = [
            {"role": msg.role.value, "content": msg.content} 
            for msg in messages
        ]
        
        # Get user context for personalization
        user_context = ChatService.get_user_context(db, user_id)
        
        # Save user message
        user_message = ChatService.add_message(
            db, conversation_id, MessageRole.USER, message
        )
        
        # Get LLM response
        try:
            assistant_response = await llm_service.get_financial_advice(
                user_message=message,
                conversation_history=conversation_history,
                user_context=user_context
            )
        except Exception as e:
            assistant_response = f"I apologize, but I'm having trouble processing your request right now. Please try again later. Error: {str(e)}"
        
        # Save assistant message
        assistant_message = ChatService.add_message(
            db, conversation_id, MessageRole.ASSISTANT, assistant_response
        )
        
        # Auto-generate title for new conversations based on first message
        if len(messages) == 0:
            title = message[:50] + "..." if len(message) > 50 else message
            ChatService.update_conversation_title(db, conversation_id, user_id, title)
        
        return {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "assistant_message": assistant_message
        }

chat_service = ChatService()