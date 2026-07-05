from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.setting import Setting
from app.models.oauth_state import OAuthState
import os
import logging
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Allow insecure transport for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_flow():
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/api/v1/auth/google/callback"
    )

@router.get("/google/url")
async def get_google_url():
    flow = get_flow()
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
    
    if not flow.code_verifier:
        raise HTTPException(status_code=500, detail="Failed to generate PKCE code verifier")
        
    oauth_state = OAuthState(state=state, code_verifier=flow.code_verifier)
    await oauth_state.insert()
    
    return {"url": auth_url}

@router.get("/google/callback")
async def google_callback(code: str, state: str):
    oauth_state = await OAuthState.find_one(OAuthState.state == state)
    if not oauth_state:
        logger.warning(f"OAuth callback failed: Invalid or expired state '{state}'")
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
    flow = get_flow()
    
    # Restore the PKCE verifier
    flow.code_verifier = oauth_state.code_verifier
    
    try:
        flow.fetch_token(code=code)
    except OAuth2Error as e:
        logger.error(f"OAuth token exchange failed: {e}")
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during token exchange")
    finally:
        # Guarantee single use by deleting the state document
        await oauth_state.delete()
        
    credentials = flow.credentials
    
    from google.oauth2 import id_token
    from google.auth.transport import requests
    
    idinfo = id_token.verify_oauth2_token(
        credentials.id_token, requests.Request(), settings.GOOGLE_CLIENT_ID
    )
    email = idinfo["email"]
    google_id = idinfo["sub"]
    
    user = await User.find_one(User.email == email)
    if not user:
        user = User(
            email=email,
            google_id=google_id,
            oauth_tokens={
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
        )
        await user.insert()
        setting = Setting(user_id=user.id)
        await setting.insert()
    else:
        user.oauth_tokens["access_token"] = credentials.token
        if credentials.refresh_token:
            user.oauth_tokens["refresh_token"] = credentials.refresh_token
        if credentials.expiry:
            user.oauth_tokens["expiry"] = credentials.expiry.isoformat()
        await user.save()
        
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return RedirectResponse(url=f"http://localhost:5173/auth/success?token={access_token}")
