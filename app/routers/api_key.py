from fastapi import APIRouter, Depends, HTTPException
from app.config.settings import settings
from app.middleware.jwt_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/key", tags=["api-keys"])

@router.get("/alpha-vantage")
async def get_alpha_vantage_api_key(current_user: User = Depends(get_current_user)):
    if not settings.ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key not configured"
        )
    return {"apiKey": settings.ALPHA_VANTAGE_API_KEY}

@router.get("/rapid-api")
async def get_rapid_api_key(current_user: User = Depends(get_current_user)):
    if not settings.RAPID_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Rapid API key not configured"
        )
    return {"apiKey": settings.RAPID_API_KEY}