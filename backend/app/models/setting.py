from beanie import Document
from datetime import datetime, timezone
from typing import List
from beanie import PydanticObjectId

class Setting(Document):
    user_id: PydanticObjectId
    reminder_frequency_minutes: int = 60
    notification_channels: List[str] = ["browser"]
    auto_generate_drafts: bool = True
    updated_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "settings"
