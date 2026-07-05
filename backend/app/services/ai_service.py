import os
import logging
import asyncio
import json
from typing import Dict, Any
from google import genai
from pydantic import BaseModel, Field
from app.models.user import User
from app.models.email import Email
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.config import settings

logger = logging.getLogger(__name__)

# Pydantic schema for structured Gemini output
class TaskExtractionSchema(BaseModel):
    actionable: bool
    title: str = Field(description="Short title for the task")
    description: str = Field(description="Detailed description of what needs to be done")
    deadline: str = Field(description="Deadline mentioned in the email, or empty string if none")
    priority: str = Field(description="High, Medium, or Low")
    category: str = Field(description="Category of the task")
    summary: str = Field(description="Short summary of the email context")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0 that this extraction is correct")

async def analyze_emails(user: User) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Fetch un-analyzed emails
    emails_to_analyze = await Email.find(
        Email.user_id == user.id,
        Email.is_analyzed == False
    ).to_list()
    
    logger.info(f"Found {len(emails_to_analyze)} emails to analyze for user {user.email}")
    
    tasks_created = 0
    emails_processed = 0
    new_tasks = []
    
    for email in emails_to_analyze:
        try:
            body_content = email.plain_text if email.plain_text else email.html_body
            if not body_content:
                body_content = email.snippet
                
            prompt = f"""
            Analyze the following email and determine if it contains an actionable task for the recipient.
            If it does, extract the task details. If it doesn't, mark actionable as false.
            
            Email Subject: {email.subject}
            From: {email.sender}
            Date: {email.date.isoformat() if email.date else ''}
            
            Body:
            {body_content[:3000]}
            """
            
            response = await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': TaskExtractionSchema,
                    'temperature': 0.1,
                }
            )
            
            # Rate limit backoff for Gemini free tier (Fix #1)
            await asyncio.sleep(10)
            
            result_dict = json.loads(response.text)
            
            if result_dict.get('actionable'):
                priority_str = result_dict.get('priority', 'Medium').capitalize()
                if priority_str not in ["High", "Medium", "Low"]:
                    priority_str = "Medium"
                    
                priority_enum = TaskPriority(priority_str)
                
                new_task = Task(
                    user_id=user.id,
                    email_id=email.id,
                    title=result_dict.get('title', 'Untitled Task'),
                    description=result_dict.get('description', ''),
                    deadline=result_dict.get('deadline') or None,
                    priority=priority_enum,
                    category=result_dict.get('category', 'General'),
                    summary=result_dict.get('summary', ''),
                    confidence=float(result_dict.get('confidence', 1.0)),
                    status=TaskStatus.PENDING
                )
                await new_task.insert()
                new_tasks.append(new_task)
                tasks_created += 1
                
        except Exception as e:
            logger.error(f"Error analyzing email {email.id}: {e}")
            
        # Always mark as analyzed to prevent retrying failures endlessly
        email.is_analyzed = True
        await email.save()
        emails_processed += 1
        
    return {
        "emails_processed": emails_processed,
        "tasks_created": tasks_created,
        "new_tasks": new_tasks
    }

async def draft_acknowledgement(email: Email) -> str:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = f"""
    Draft a professional, context-aware email reply to the following email.
    Tone: Standard Professional.
    
    Email Subject: {email.subject}
    From: {email.sender}
    Body:
    {email.plain_text or email.snippet}
    
    IMPORTANT: You must automatically append this exact signature block to the end of your generated email body:
    
    Best regards,
    Gourang S.
    EXTC Engineering Student
    Sardar Patel Institute of Technology
    """
    
    response = await asyncio.to_thread(
        client.models.generate_content,
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    return response.text
