from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db
from app.utils.auth import get_current_active_user
from app.tasks.clip_tasks import generate_captions, export_clip

router = APIRouter()

@router.get("/", response_model=List[schemas.ClipResponse])
async def get_user_clips(
    video_id: int = None,
    platform: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.Clip).filter(models.Clip.user_id == current_user.id)
    
    if video_id:
        query = query.filter(models.Clip.video_id == video_id)
    if platform:
        query = query.filter(models.Clip.platform == platform)
    
    clips = query.offset(skip).limit(limit).all()
    return clips

@router.get("/{clip_id}", response_model=schemas.ClipResponse)
async def get_clip(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    clip = db.query(models.Clip).filter(
        models.Clip.id == clip_id,
        models.Clip.user_id == current_user.id
    ).first()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return clip

@router.post("/{clip_id}/captions", response_model=schemas.CaptionResponse)
async def generate_clip_captions(
    clip_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    clip = db.query(models.Clip).filter(
        models.Clip.id == clip_id,
        models.Clip.user_id == current_user.id
    ).first()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Check if captions already exist
    existing_caption = db.query(models.Caption).filter(
        models.Caption.clip_id == clip_id
    ).first()
    
    if existing_caption:
        return existing_caption
    
    # Generate captions
    background_tasks.add_task(generate_captions.delay, clip_id)
    
    return {"message": "Caption generation started"}

@router.post("/{clip_id}/export")
async def export_clip_endpoint(
    clip_id: int,
    platform: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    clip = db.query(models.Clip).filter(
        models.Clip.id == clip_id,
        models.Clip.user_id == current_user.id
    ).first()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    background_tasks.add_task(export_clip.delay, clip_id, platform)
    
    return {"message": f"Clip export to {platform} started"}

@router.post("/{clip_id}/download")
async def download_clip(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    clip = db.query(models.Clip).filter(
        models.Clip.id == clip_id,
        models.Clip.user_id == current_user.id
    ).first()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Increment download count
    clip.downloads += 1
    db.commit()
    
    return {"download_url": clip.s3_url}