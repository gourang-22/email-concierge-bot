import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def send_telegram_message(text: str, chat_id: str, reply_markup: dict = None):
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send telegram message: {e}")

async def edit_telegram_message(message_id: int, chat_id: str, new_text: str, reply_markup: dict = None):
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": new_text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to edit telegram message: {e}")
