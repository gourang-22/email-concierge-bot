from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict
from app.models.user import User
from app.api.deps import get_current_user
from app.models.task import Task
from beanie import PydanticObjectId

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/")
async def get_tasks(current_user: User = Depends(get_current_user)):
    tasks = await Task.find(
        Task.user_id == current_user.id,
        Task.status == "Pending"
    ).sort(-Task.created_at).to_list()
    return tasks

@router.patch("/{task_id}")
async def update_task(task_id: str, status_data: Dict[str, str] = Body(...), current_user: User = Depends(get_current_user)):
    try:
        task_obj_id = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Task ID")
        
    task = await Task.find_one(Task.id == task_obj_id, Task.user_id == current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    new_status = status_data.get("status")
    if new_status in ["Pending", "Completed"]:
        task.status = new_status
        await task.save()
        return task
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
