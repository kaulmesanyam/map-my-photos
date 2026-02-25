from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import security
import models
from database import get_db
import photos_service

router = APIRouter(prefix="/photos", tags=["photos"])

@router.post("/sync")
async def trigger_photo_sync(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """Triggers a background or inline sync of the user's Google Photos."""
    
    try:
        synced_count = await photos_service.sync_user_photos(current_user, db)
        return {"message": "Sync successful", "synced_photos": synced_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/")
def get_user_photos(limit: int = 50, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """Returns the user's synced photos."""
    photos = db.query(models.Photo).filter(models.Photo.user_id == current_user.id).limit(limit).all()
    return photos
