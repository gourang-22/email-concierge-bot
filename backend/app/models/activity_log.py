from beanie import Document

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from beanie import PydanticObjectId

class ActivityLog(Document):
    user_id: PydanticObjectId
    task_id: PydanticObjectId
    action: str # STATUS_CHANGED, DRAFT_EDITED, EMAIL_REPLIED, DEADLINE_UPDATED
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "activityLogs"
