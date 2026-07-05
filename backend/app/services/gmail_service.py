from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.services.oauth_service import get_valid_credentials
import base64
import logging
import asyncio

logger = logging.getLogger(__name__)

async def get_gmail_service(user):
    creds = await get_valid_credentials(user)
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)

def parse_parts(parts, attachments):
    plain_text = ""
    html_body = ""
    for part in parts:
        mime_type = part.get('mimeType')
        body = part.get('body')
        data = body.get('data')
        
        if part.get('filename'):
            # It's an attachment
            attachments.append({
                "attachment_id": body.get('attachmentId', ''),
                "filename": part.get('filename'),
                "mime_type": mime_type,
                "size": body.get('size', 0)
            })
        elif mime_type == 'text/plain' and data:
            plain_text += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        elif mime_type == 'text/html' and data:
            html_body += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        elif part.get('parts'):
            # Recurse
            sub_plain, sub_html = parse_parts(part.get('parts'), attachments)
            plain_text += sub_plain
            html_body += sub_html
            
    return plain_text, html_body

async def get_message(user, message_id: str):
    try:
        service = await get_gmail_service(user)
        msg = await asyncio.to_thread(
            service.users().messages().get(userId='me', id=message_id, format='full').execute
        )
        
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        recipients_str = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
        cc_str = next((h['value'] for h in headers if h['name'].lower() == 'cc'), '')
        bcc_str = next((h['value'] for h in headers if h['name'].lower() == 'bcc'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '') 
        
        recipients = [r.strip() for r in recipients_str.split(',')] if recipients_str else []
        cc = [c.strip() for c in cc_str.split(',')] if cc_str else []
        bcc = [b.strip() for b in bcc_str.split(',')] if bcc_str else []
        
        attachments = []
        plain_text, html_body = "", ""
        
        if 'parts' in payload:
            plain_text, html_body = parse_parts(payload.get('parts'), attachments)
        else:
            body = payload.get('body', {}).get('data', '')
            if body:
                decoded = base64.urlsafe_b64decode(body).decode('utf-8', errors='replace')
                if payload.get('mimeType') == 'text/html':
                    html_body = decoded
                else:
                    plain_text = decoded
                    
        return {
            "gmail_id": msg['id'],
            "thread_id": msg['threadId'],
            "subject": subject,
            "sender": sender,
            "recipients": recipients,
            "cc": cc,
            "bcc": bcc,
            "date_str": date,
            "labels": msg.get('labelIds', []),
            "snippet": msg.get('snippet', ''),
            "plain_text": plain_text,
            "html_body": html_body,
            "attachments": attachments,
            "is_unread": 'UNREAD' in msg.get('labelIds', []),
            "is_starred": 'STARRED' in msg.get('labelIds', []),
            "history_id": msg.get('historyId')
        }
    except HttpError as e:
        logger.error(f"Gmail API error for user {user.email}: {e}")
        raise
        
async def list_messages(user, max_results=100, page_token=None):
    service = await get_gmail_service(user)
    kwargs = {'userId': 'me', 'maxResults': max_results, 'q': 'is:unread'}
    if page_token:
        kwargs['pageToken'] = page_token
    return await asyncio.to_thread(service.users().messages().list(**kwargs).execute)

async def list_history(user, start_history_id):
    service = await get_gmail_service(user)
    return await asyncio.to_thread(
        service.users().history().list(userId='me', startHistoryId=start_history_id).execute
    )

from email.message import EmailMessage

async def send_reply(user, thread_id: str, to: str, subject: str, text: str):
    service = await get_gmail_service(user)
    
    message = EmailMessage()
    message.set_content(text)
    message['To'] = to
    
    if not subject.lower().startswith('re:'):
        subject = 'Re: ' + subject
    message['Subject'] = subject
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {
        'raw': encoded_message,
        'threadId': thread_id
    }
    
    return await asyncio.to_thread(
        service.users().messages().send(userId='me', body=create_message).execute
    )
