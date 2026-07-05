from beanie import Document
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from beanie import PydanticObjectId

class TaskStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"

class TaskPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class WorkflowState(str, Enum):
    ACTION_REQUIRED = "Action Required"
    DRAFTING = "Drafting"
    PENDING_APPROVAL = "Pending Approval"
    SENT = "Sent"
    DISCARDED = "Discarded"
    NO_REPLY = "No Reply"
    COMPLETED = "Completed"

class Task(Document):
    user_id: PydanticObjectId
    email_id: PydanticObjectId
    title: str
    description: str
    deadline: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    category: str
    summary: str
    confidence: float
    status: TaskStatus = TaskStatus.PENDING
    workflow_state: WorkflowState = WorkflowState.ACTION_REQUIRED
    is_notified: bool = False
    created_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "tasks"
