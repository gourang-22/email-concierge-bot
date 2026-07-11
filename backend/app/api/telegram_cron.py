from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from app.services.sync_service import sync_user_emails
from app.services.ai_service import analyze_emails, draft_acknowledgement
from app.services.telegram_service import send_telegram_message
from app.services.gmail_service import send_reply
from app.models.user import User
from app.models.task import Task, WorkflowState, TaskStatus
from app.models.email import Email
from app.core.config import settings
from beanie import PydanticObjectId
from beanie.operators import In
from pydantic import BaseModel
import logging
import os
import asyncio
import httpx
from google import genai

class SendReplyRequest(BaseModel):
    draft_text: str

router = APIRouter(tags=["telegram_cron"])
logger = logging.getLogger(__name__)

@router.get("/telegram/set-webhook")
async def set_telegram_webhook(request: Request):
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")
        
    # Extract the base URL from the incoming request (which would be the ngrok URL)
    base_url = str(request.base_url).rstrip("/")
    webhook_url = f"{base_url}/api/v1/telegram/webhook"
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"url": webhook_url})
            resp.raise_for_status()
            return {"status": "ok", "webhook_url": webhook_url, "telegram_response": resp.json()}
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def process_cron_sync():
    users = await User.find_all().to_list()
    for user in users:
        try:
            await sync_user_emails(user)
            result = await analyze_emails(user)
            
            new_tasks = result.get("new_tasks", [])
            if new_tasks:
                text = f"📬 You have {len(new_tasks)} new pending tasks waiting for your action."
                
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "Open Inbox", 
                                "web_app": {"url": settings.TELEGRAM_WEBAPP_URL}
                            }
                        ]
                    ]
                }
                if settings.TELEGRAM_CHAT_ID and settings.TELEGRAM_WEBAPP_URL:
                    await send_telegram_message(text, settings.TELEGRAM_CHAT_ID, reply_markup)
                else:
                    logger.warning("TELEGRAM_CHAT_ID or TELEGRAM_WEBAPP_URL not configured. Could not send Web App notification.")
        except Exception as e:
            logger.error(f"Error syncing user {user.email}: {e}")

@router.get("/cron/sync")
async def cron_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_cron_sync)
    return {"status": "ok", "message": "Sync started in the background"}

@router.get("/webapp", response_class=HTMLResponse)
async def serve_webapp():
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "webapp.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Webapp template not found.")

@router.get("/webapp/tasks")
async def get_webapp_tasks():
    # Fetch tasks that require action
    tasks = await Task.find(
        In(Task.workflow_state, [WorkflowState.ACTION_REQUIRED, WorkflowState.DRAFTING, WorkflowState.PENDING_APPROVAL])
    ).sort(-Task.created_at).to_list()

    
    # Sort tasks by priority logically
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    tasks.sort(key=lambda t: priority_order.get(t.priority.value if hasattr(t.priority, 'value') else t.priority, 4))
    
    # We serialize the ObjectId properly and attach the email's thread_id
    result = []
    for task in tasks:
        task_dict = task.dict()
        task_dict["_id"] = str(task.id)
        email = await Email.get(task.email_id)
        task_dict["thread_id"] = email.thread_id if email else ""
        result.append(task_dict)
    return result

@router.post("/webapp/tasks/{task_id}/draft")
async def draft_task_reply(task_id: str):
    task = await Task.get(PydanticObjectId(task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    email = await Email.get(task.email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    task.workflow_state = WorkflowState.DRAFTING
    await task.save()
    
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    body_content = email.plain_text if email.plain_text else email.html_body
    if not body_content:
        body_content = email.snippet
        
    prompt = f"""
    You are Gourang S., a second-year EXTC engineering student at Sardar Patel Institute of Technology. Write a concise, professional reply to the following email context. Always append an official student signature block at the bottom containing my name, degree, and institution.
    
    Email Context:
    {body_content}
    """
    
    response = await asyncio.to_thread(
        client.models.generate_content,
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    draft = response.text
    
    task.workflow_state = WorkflowState.PENDING_APPROVAL
    task.description = draft
    await task.save()
    
    return {"status": "ok", "draft": draft}

@router.post("/webapp/tasks/{task_id}/send")
async def send_task_reply(task_id: str, request: SendReplyRequest):
    task = await Task.get(PydanticObjectId(task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    email = await Email.get(task.email_id)
    user = await User.get(task.user_id)
    
    if email and user:
        await send_reply(
            user=user,
            thread_id=email.thread_id,
            to=email.sender,
            subject=email.subject,
            text=request.draft_text
        )
        task.description = request.draft_text
        task.workflow_state = WorkflowState.SENT
        task.status = TaskStatus.COMPLETED
        await task.save()
        return {"status": "ok"}
    raise HTTPException(status_code=500, detail="Failed to send email")

@router.post("/webapp/tasks/{task_id}/done")
async def mark_task_done(task_id: str):
    task = await Task.get(PydanticObjectId(task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.workflow_state = WorkflowState.COMPLETED
    task.status = TaskStatus.COMPLETED
    await task.save()
    return {"status": "ok"}
