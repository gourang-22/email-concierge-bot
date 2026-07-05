from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.api.deps import get_current_user
from app.services.ai_service import analyze_emails

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/analyze")
async def trigger_analysis(current_user: User = Depends(get_current_user)):
    try:
        result = await analyze_emails(current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
