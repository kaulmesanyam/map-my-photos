import os
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
import models

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

async def get_google_access_token(user: models.User) -> str:
    """Gets a fresh access token using the user's refresh token."""
    if not user.google_refresh_token:
        raise HTTPException(status_code=400, detail="User has no Google refresh token. Please re-login.")
        
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": user.google_refresh_token,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to refresh Google access token.")
            
        tokens = response.json()
        return tokens["access_token"]

async def sync_user_photos(user: models.User, db: Session):
    """Fetches recent photos from Google Photos API and saves them to the DB."""
    access_token = await get_google_access_token(user)
    
    # We will fetch only up to 50 items for MVP initial sync
    photos_url = "https://photoslibrary.googleapis.com/v1/mediaItems"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"pageSize": 50}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(photos_url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching photos: {response.text}")
            raise HTTPException(status_code=400, detail="Failed to fetch photos from Google")
            
        data = response.json()
        media_items = data.get("mediaItems", [])
        
        synced_count = 0
        for item in media_items:
            # We only want photos (skip videos for MVP unless needed)
            if "photo" not in item.get("mediaMetadata", {}):
                print(f"Skipping non-photo item: {item['id']}")
                continue
                
            google_photo_id = item["id"]
            
            # Check if we already have it
            existing = db.query(models.Photo).filter(models.Photo.google_photo_id == google_photo_id).first()
            if existing:
                print(f"Skipping duplicate photo: {google_photo_id}")
                continue
                
            # Parse metadata
            metadata = item.get("mediaMetadata", {})
            creation_time = metadata.get("creationTime") # string format standard
            
            # thumbnail url (adding =w512-h512 to get a specific size, or use baseUrl directly)
            base_url = item["baseUrl"]
            thumbnail_url = f"{base_url}=w512-h512"
            
            # Create new Photo record (No embeddings or lat/lon yet)
            photo_record = models.Photo(
                user_id=user.id,
                google_photo_id=google_photo_id,
                thumbnail_url=thumbnail_url,
                # creation_time handling might require parsing to datetime
            )
            db.add(photo_record)
            synced_count += 1
            
        db.commit()
        return synced_count
