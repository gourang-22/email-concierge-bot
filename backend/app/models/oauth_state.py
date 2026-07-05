from beanie import Document, Indexed
from datetime import datetime, timezone
from pydantic import Field
import pymongo

class OAuthState(Document):
    state: Indexed(str, unique=True)
    code_verifier: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "oauth_states"
        indexes = [
            pymongo.IndexModel([("created_at", pymongo.ASCENDING)], expireAfterSeconds=600)
        ]
