from app.services.gmail_service import list_messages, list_history, get_message
from app.models.email import Email, AttachmentMetadata
from app.models.user import User
import logging
from datetime import datetime, timezone
import email.utils

logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> datetime:
    try:
        if not date_str:
            return datetime.now(timezone.utc)
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed
    except Exception:
        return datetime.now(timezone.utc)

async def sync_user_emails(user: User):
    logger.info(f"Starting email sync for {user.email}")
    
    new_message_ids = set()
    latest_history_id = user.last_history_id
    
    try:
        if user.last_history_id:
            # Incremental sync
            logger.info(f"Performing incremental sync from historyId {user.last_history_id}")
            history_response = await list_history(user, user.last_history_id)
            history_records = history_response.get('history', [])
            
            for record in history_records:
                for msg_added in record.get('messagesAdded', []):
                    new_message_ids.add(msg_added['message']['id'])
            
            latest_history_id = history_response.get('historyId', user.last_history_id)
        else:
            # Full sync (limited to 5 for demo)
            logger.info("Performing initial full sync (limit 5 for demo)")
            messages_response = await list_messages(user, max_results=5)
            messages = messages_response.get('messages', [])
            
            for msg in messages:
                new_message_ids.add(msg['id'])
                
        imported_count = 0
        
        for msg_id in new_message_ids:
            # Check for duplicate
            exists = await Email.find_one(Email.gmail_id == msg_id)
            if exists:
                continue
                
            try:
                msg_data = await get_message(user, msg_id)
            except Exception as e:
                if "404" in str(e):
                    logger.warning(f"Email {msg_id} not found (404). Skipping.")
                    continue
                raise
            
            attachments = []
            for att in msg_data.get('attachments', []):
                attachments.append(AttachmentMetadata(
                    attachment_id=att['attachment_id'],
                    filename=att['filename'],
                    mime_type=att['mime_type'],
                    size=att['size']
                ))
                
            new_email = Email(
                user_id=user.id,
                gmail_id=msg_data['gmail_id'],
                thread_id=msg_data['thread_id'],
                subject=msg_data['subject'],
                sender=msg_data['sender'],
                recipients=msg_data['recipients'],
                cc=msg_data['cc'],
                bcc=msg_data['bcc'],
                date=parse_date(msg_data['date_str']),
                labels=msg_data['labels'],
                snippet=msg_data['snippet'],
                plain_text=msg_data['plain_text'],
                html_body=msg_data['html_body'],
                attachments=attachments,
                is_unread=msg_data['is_unread'],
                is_starred=msg_data['is_starred']
            )
            await new_email.insert()
            imported_count += 1
            
            if not latest_history_id and msg_data.get('history_id'):
                latest_history_id = msg_data['history_id']
                
        if latest_history_id:
            user.last_history_id = str(latest_history_id)
            await user.save()
            
        logger.info(f"Sync complete for {user.email}. Imported {imported_count} new emails.")
        return {"status": "success", "imported": imported_count}
        
    except Exception as e:
        logger.error(f"Failed to sync emails for {user.email}: {e}")
        raise
