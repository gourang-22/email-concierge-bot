from beanie import Document
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from beanie import PydanticObjectId

class NotificationType(str, Enum):
    DEADLINE_APPROACHING = "DEADLINE_APPROACHING"
    OVERDUE = "OVERDUE"
    DAILY_SUMMARY = "DAILY_SUMMARY"
    NEW_TASK = "NEW_TASK"

class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    DISMISSED = "DISMISSED"

class Notification(Document):
    user_id: PydanticObjectId
    task_id: Optional[PydanticObjectId] = None
    type: NotificationType
    status: NotificationStatus = NotificationStatus.UNREAD
    message: str
    created_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "notifications"
