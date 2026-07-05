import google.oauth2.credentials
from google.auth.transport.requests import Request
from app.models.user import User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def get_valid_credentials(user: User):
    if not user.oauth_tokens:
        raise ValueError("User has no OAuth tokens")
        
    creds = google.oauth2.credentials.Credentials(
        token=user.oauth_tokens.get("access_token"),
        refresh_token=user.oauth_tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    
    if creds.expired and creds.refresh_token:
        try:
            logger.info(f"Refreshing expired token for user {user.email}")
            creds.refresh(Request())
            user.oauth_tokens["access_token"] = creds.token
            if creds.expiry:
                user.oauth_tokens["expiry"] = creds.expiry.isoformat()
            await user.save()
        except Exception as e:
            logger.error(f"Failed to refresh token for user {user.email}: {e}")
            raise ValueError("Failed to refresh OAuth token") from e
            
    return creds
