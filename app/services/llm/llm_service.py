import httpx
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        self.model = "Qwen/Qwen2.5-7B-Instruct:together"
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        
        # Financial coach system prompt
        self.system_prompt = """You are an expert financial coach and trading advisor. Your role is to:
- Provide educational guidance on trading, investing, and financial markets
- Help users understand market concepts, technical analysis, and risk management
- Analyze trading scenarios and portfolio decisions
- Offer personalized advice based on user's trading history and goals
- Explain financial concepts in clear, accessible language
- Encourage responsible trading practices and risk awareness

Always be supportive, educational, and cautious about risk. Never guarantee returns or encourage reckless trading."""

    async def query_model(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 500, 
        temperature: float = 0.7
    ) -> str:
        """Query the Hugging Face Router API with chat completion format"""
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract content from chat completion format
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception("Unexpected response format from API")
                    
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except httpx.HTTPError as e:
            raise Exception(f"LLM API connection error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def build_messages(
        self, 
        conversation_history: List[Dict[str, str]], 
        new_message: str,
        user_context: Dict = None
    ) -> List[Dict[str, str]]:
        """Build messages array in chat completion format"""
        messages = []
        
        # Add system message
        system_content = self.system_prompt
        
        # Add user context to system message if provided
        if user_context:
            context_parts = []
            if user_context.get("portfolio_value"):
                context_parts.append(f"User's total portfolio value: ${user_context['portfolio_value']:.2f}")
            if user_context.get("cash_balance"):
                context_parts.append(f"Available cash: ${user_context['cash_balance']:.2f}")
            if user_context.get("invested_amount"):
                context_parts.append(f"Currently invested: ${user_context['invested_amount']:.2f}")
            
            if context_parts:
                system_content += "\n\nUser Context:\n" + "\n".join(context_parts)
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add recent conversation history (last 8 messages to manage context)
        recent_messages = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
        
        for msg in recent_messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add new user message
        messages.append({
            "role": "user",
            "content": new_message
        })
        
        return messages

    async def get_financial_advice(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]] = None,
        user_context: Dict = None
    ) -> str:
        """Get financial advice with context"""
        
        # Build messages in chat completion format
        if conversation_history is None:
            conversation_history = []
            
        messages = self.build_messages(
            conversation_history=conversation_history,
            new_message=user_message,
            user_context=user_context
        )
        
        # Get response from model
        response = await self.query_model(
            messages=messages,
            max_tokens=800,  # Increased for more detailed responses
            temperature=0.7
        )
        
        return response.strip()

# Singleton instance
llm_service = LLMService()