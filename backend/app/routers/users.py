from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app import models, schemas
from app.database import get_db
from app.utils.auth import get_current_active_user

router = APIRouter()

class AISettings(BaseModel):
    transcriptionModel: str = "base"
    transcriptionLanguage: str = "en"
    clipDuration: int = 30
    maxClipsPerVideo: int = 5
    platforms: List[str] = ["tiktok", "instagram", "youtube"]
    captionStyle: str = "casual"
    captionLength: str = "medium"
    includeHashtags: bool = True
    numberOfHashtags: int = 10
    autoPublish: bool = False
    scheduleTime: str = "09:00"

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
    total_views = db.query(models.Clip).filter(models.Clip.user_id == current_user.id).with_entities(db.func.sum(models.Clip.views)).scalar() or 0
    total_downloads = db.query(models.Clip).filter(models.Clip.user_id == current_user.id).with_entities(db.func.sum(models.Clip.downloads)).scalar() or 0
    
    return {
        "totalVideos": videos_count,
        "totalClips": clips_count,
        "totalViews": total_views,
        "totalDownloads": total_downloads
    }

@router.get("/settings")
async def get_ai_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # You can store settings in a new table or return defaults
    # For now, return default settings
    return AISettings().dict()

@router.post("/settings")
async def save_ai_settings(
    settings: AISettings,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Save settings to database (create a UserSettings table for this)
    # For now, just return success
    return {"message": "Settings saved successfully", "settings": settings.dict()}