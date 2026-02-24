import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Scopes needed for basic profile and reading Google Photos
SCOPES = "openid email profile https://www.googleapis.com/auth/photoslibrary.readonly"

@router.get("/login")
def login_via_google():
    """Redirects the user to the Google OAuth login page."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID is not configured.")
        
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"scope={SCOPES}&"
        "access_type=offline&" # Ask for a refresh token
        "prompt=consent"
    )
    return RedirectResponse(auth_url)

@router.get("/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handles the callback from Google, exchanges the code for tokens."""
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Exchange 'code' for access token & refresh token
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange token with Google")
            
        tokens = response.json()
        access_token = tokens.get("access_token")
        
        # 2. Get User Info
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = await client.get(user_info_url, headers=headers)
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
            
        user_data = user_response.json()
        
        # 3. Save or Update User in DB
        google_id = user_data.get("id")
        email = user_data.get("email")
        name = user_data.get("name")
        
        user = db.query(models.User).filter(models.User.google_id == google_id).first()
        if not user:
            user = models.User(google_id=google_id, email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # For the MVP, we can just return the tokens or set a cookie.
        # In a real app, you'd generate a JWT session token here and store the refresh token
        # to fetch photos later. 
        return {
            "message": "Login successful", 
            "user": {"email": email, "name": name},
            "credentials_for_photos_api": {
                "access_token": access_token,
                "refresh_token": tokens.get("refresh_token")
            }
        }
