from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.api.deps import get_current_user
from app.services.sync_service import sync_user_emails
from app.models.email import Email

router = APIRouter(prefix="/gmail", tags=["gmail"])

@router.post("/sync")
async def trigger_sync(current_user: User = Depends(get_current_user)):
    try:
        result = await sync_user_emails(current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails")
async def get_synchronized_emails(current_user: User = Depends(get_current_user), limit: int = 50):
    emails = await Email.find(Email.user_id == current_user.id).sort(-Email.date).limit(limit).to_list()
    return emails
