import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.sync_service import sync_user_emails
from app.services.ai_service import analyze_emails
from app.services.notification_service import check_and_notify_tasks
from app.models.user import User

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_workflow():
    logger.info("Running scheduled proactive workflow...")
    users = await User.find_all().to_list()
    for user in users:
        # 1. Sync Gmail
        try:
            await sync_user_emails(user)
        except Exception as e:
            logger.error(f"Scheduled sync failed for {user.email}: {e}")
            
        # 2. Analyze Emails
        try:
            await analyze_emails(user)
        except Exception as e:
            logger.error(f"Scheduled AI analysis failed for {user.email}: {e}")
            
        # 3. Send Notifications
        try:
            await check_and_notify_tasks()
        except Exception as e:
            logger.error(f"Scheduled notification failed: {e}")

def start_scheduler():
    scheduler.add_job(scheduled_workflow, 'interval', minutes=180)
    scheduler.start()
    logger.info("Proactive background scheduler started (180-minute intervals).")
