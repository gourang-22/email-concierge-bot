from pymongo.asynchronous.mongo_client import AsyncMongoClient
from beanie import init_beanie
from app.core.config import settings

from app.models.user import User
from app.models.setting import Setting
from app.models.task import Task
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.models.email import Email
from app.models.oauth_state import OAuthState

async def init_db():
    client = AsyncMongoClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            User,
            Setting,
            Task,
            Notification,
            ActivityLog,
            Email,
            OAuthState
        ]
    )
