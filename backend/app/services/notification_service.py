import logging
from app.models.task import Task
from app.models.email import Email
import asyncio
from win11toast import toast

logger = logging.getLogger(__name__)

async def check_and_notify_tasks():
    logger.info("Checking for un-notified tasks...")
    tasks = await Task.find(
        Task.is_notified == False,
        Task.status == "Pending"
    ).to_list()
    
    if not tasks:
        logger.info("No new tasks to notify.")
        return
        
    for task in tasks:
        email = await Email.get(task.email_id)
        if email:
            thread_url = f"https://mail.google.com/mail/u/0/#all/{email.thread_id}"
            
            def send_toast():
                body_text = f"Priority: {task.priority}\n"
                if task.deadline:
                    body_text += f"Deadline: {task.deadline}"
                else:
                    body_text += "No deadline"
                    
                buttons = [
                    {'activationType': 'protocol', 'arguments': thread_url, 'content': 'Read Mail'},
                    {'activationType': 'protocol', 'arguments': 'http://localhost:5173/dashboard', 'content': 'Reply'}
                ]
                
                toast(
                    f"New Task: {task.title}",
                    body_text,
                    buttons=buttons,
                    audio={'src': 'ms-winsoundevent:Notification.Default'}
                )
            
            try:
                await asyncio.to_thread(send_toast)
                task.is_notified = True
                await task.save()
                logger.info(f"Notified user about task: {task.title}")
            except Exception as e:
                logger.error(f"Failed to send toast notification for task {task.id}: {e}")
