from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
import logging
from app import models, schemas, utils
from app.database import get_db
from app.utils.auth import get_current_active_user
from app.utils.storage import upload_to_s3
from app.tasks.video_tasks import process_video
from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=schemas.VideoResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None),  # Changed to Form to handle form data properly
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    logger.info(f"Upload request received from user {current_user.id}")
    logger.info(f"File: {file.filename}, Content-Type: {file.content_type}")
    
    # Validate file type
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
        logger.error(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {settings.ALLOWED_VIDEO_TYPES}")
    
    # Read file content
    try:
        content = await file.read()
        file_size = len(content)
        logger.info(f"File size: {file_size} bytes")
        
        # Reset file position for potential re-reading
        await file.seek(0)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(status_code=500, detail="Error reading file")
    
    # Check file size
    if file_size > settings.MAX_UPLOAD_SIZE:
        logger.error(f"File too large: {file_size} > {settings.MAX_UPLOAD_SIZE}")
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    s3_key = f"videos/{current_user.id}/{uuid.uuid4()}{file_extension}"
    logger.info(f"Generated S3 key: {s3_key}")
    
    # For development without S3, save locally
    try:
        # Try S3 first
        s3_url = await upload_to_s3(content, s3_key, file.content_type)
        logger.info(f"Uploaded to S3: {s3_url}")
    except Exception as e:
        logger.warning(f"S3 upload failed: {e}. Falling back to local storage.")
        # Fallback to local storage
        import aiofiles
        os.makedirs("uploads", exist_ok=True)
        local_path = f"uploads/{s3_key.split('/')[-1]}"
        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(content)
        s3_url = f"http://localhost:8000/uploads/{s3_key.split('/')[-1]}"
        logger.info(f"Saved locally: {local_path}")
    
    # Create video record
    try:
        db_video = models.Video(
            user_id=current_user.id,
            title=title or file.filename,
            description=description,
            filename=file.filename,
            file_size=file_size,
            s3_key=s3_key,
            s3_url=s3_url,
            status="pending"
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        logger.info(f"Video record created: {db_video.id}")
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create video record")
    
    # Trigger background processing
    try:
        background_tasks.add_task(process_video.delay, db_video.id)
        logger.info(f"Background task added for video {db_video.id}")
    except Exception as e:
        logger.warning(f"Failed to start background task: {e}")
        # Still return success as video is uploaded
    
    return db_video

@router.get("/", response_model=List[schemas.VideoResponse])
async def get_user_videos(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    videos = db.query(models.Video).filter(
        models.Video.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return videos

@router.get("/{video_id}", response_model=schemas.VideoResponse)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video

@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete from storage
    try:
        await utils.storage.delete_from_s3(video.s3_key)
    except Exception as e:
        logger.warning(f"Failed to delete from storage: {e}")
    
    # Delete from database
    db.delete(video)
    db.commit()
    
    return {"message": "Video deleted successfully"}

@router.post("/{video_id}/process")
async def process_video_manually(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    background_tasks.add_task(process_video.delay, video_id)
    
    return {"message": "Video processing started"}