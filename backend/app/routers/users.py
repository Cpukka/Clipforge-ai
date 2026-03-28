from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user

@router.get("/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    videos_count = db.query(models.Video).filter(models.Video.user_id == current_user.id).count()
    clips_count = db.query(models.Clip).filter(models.Clip.user_id == current_user.id).count()
    
    return {
        "totalVideos": videos_count,
        "totalClips": clips_count,
        "totalViews": 0,  # Implement view tracking
        "totalDownloads": 0  # Implement download tracking
    }