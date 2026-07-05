from beanie import Document
from datetime import datetime, timezone
from typing import Optional, Dict

class User(Document):
    email: str
    google_id: str
    oauth_tokens: Dict[str, str] # access_token, refresh_token, expiry
    last_history_id: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "users"
