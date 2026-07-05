from beanie import Document, Indexed
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from beanie import PydanticObjectId

class AttachmentMetadata(BaseModel):
    attachment_id: str
    filename: str
    mime_type: str
    size: int

class Email(Document):
    user_id: PydanticObjectId
    gmail_id: Indexed(str, unique=True)
    thread_id: str
    subject: str
    sender: str
    recipients: List[str] = []
    cc: List[str] = []
    bcc: List[str] = []
    date: datetime
    labels: List[str] = []
    snippet: str = ""
    plain_text: str = ""
    html_body: str = ""
    attachments: List[AttachmentMetadata] = []
    is_unread: bool = True
    is_starred: bool = False
    is_analyzed: bool = False
    imported_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "emails"
