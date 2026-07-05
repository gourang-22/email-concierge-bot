from fastapi import APIRouter, Depends, HTTPException
from app.models.setting import Setting
from app.models.user import User
from app.api.deps import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingUpdate(BaseModel):
    reminder_frequency_minutes: int
    notification_channels: List[str]
    auto_generate_drafts: bool

@router.get("/")
async def get_settings(current_user: User = Depends(get_current_user)):
    setting = await Setting.find_one(Setting.user_id == current_user.id)
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not found")
    return setting

@router.put("/")
async def update_settings(update_data: SettingUpdate, current_user: User = Depends(get_current_user)):
    setting = await Setting.find_one(Setting.user_id == current_user.id)
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not found")
        
    setting.reminder_frequency_minutes = update_data.reminder_frequency_minutes
    setting.notification_channels = update_data.notification_channels
    setting.auto_generate_drafts = update_data.auto_generate_drafts
    
    await setting.save()
    return setting
