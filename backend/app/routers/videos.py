from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
import logging
import subprocess
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
    title: str = Form(None),
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
    
    # Save locally (bypass S3 for development)
    try:
        import aiofiles
        os.makedirs("uploads", exist_ok=True)
        local_filename = f"{uuid.uuid4()}{file_extension}"
        local_path = f"uploads/{local_filename}"
        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(content)
        s3_url = f"http://localhost:8000/uploads/{local_filename}"
        logger.info(f"✅ Video saved locally: {local_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save video file")
    
    # Try to get video duration using ffmpeg (optional)
    duration = None
    try:
        import ffmpeg
        probe = ffmpeg.probe(local_path)
        duration = float(probe['format']['duration'])
        logger.info(f"Video duration: {duration} seconds")
    except Exception as e:
        duration = 60  # Default duration
        logger.warning(f"Could not get video duration: {e}, using default: 60s")
    
    # Create video record - Set to COMPLETED immediately for instant playback
    try:
        db_video = models.Video(
            user_id=current_user.id,
            title=title or file.filename,
            description=description,
            filename=file.filename,
            file_size=file_size,
            duration=duration,
            s3_key=s3_key,
            s3_url=s3_url,
            status="completed",  # Changed from "pending" to "completed" for instant playback
            processing_progress=100  # Set to 100% complete
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        logger.info(f"✅ Video record created: {db_video.id} (status: completed)")
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create video record")
    
    # Optional: Trigger background processing for AI features (won't affect playback)
    # This runs in background and won't block the response
    try:
        background_tasks.add_task(process_video.delay, db_video.id)
        logger.info(f"Background task added for video {db_video.id}")
    except Exception as e:
        logger.warning(f"Failed to start background task: {e}")
        # Still return success as video is uploaded and playable
    
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
    ).order_by(models.Video.created_at.desc()).offset(skip).limit(limit).all()
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
    
    # Delete file from local storage
    try:
        if video.s3_url:
            local_filename = video.s3_url.split("/")[-1]
            local_path = f"uploads/{local_filename}"
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info(f"Deleted file: {local_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file: {e}")
    
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
    
    # Trigger AI processing for clip generation
    background_tasks.add_task(process_video.delay, video_id)
    
    return {"message": "AI processing started for clip generation"}

# NEW ENDPOINT: Generate a clip from video
@router.post("/{video_id}/generate-clip")
async def generate_simple_clip(
    video_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    platform = request.get("platform", "tiktok")
    duration = request.get("duration", 30)
    
    # Get the video file path
    if video.s3_url and video.s3_url.startswith('http://localhost'):
        filename = video.s3_url.split("/")[-1]
        video_path = f"uploads/{filename}"
    else:
        raise HTTPException(status_code=400, detail="Video file not found locally")
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Create clips directory if it doesn't exist
    os.makedirs("uploads/clips", exist_ok=True)
    
    # Generate unique clip filename
    clip_filename = f"clip_{uuid.uuid4()}.mp4"
    clip_path = f"uploads/clips/{clip_filename}"
    
    try:
        # Use ffmpeg to cut the first X seconds of the video
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-t', str(duration),
            '-c', 'copy',
            clip_path
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Failed to generate clip: {result.stderr}")
        
        logger.info(f"✅ Clip generated: {clip_path}")
        
        # Create clip record in database
        clip = models.Clip(
            user_id=current_user.id,
            video_id=video_id,
            title=f"{video.title} - {platform.upper()} Clip",
            start_time=0,
            end_time=duration,
            s3_key=f"clips/{clip_filename}",
            s3_url=f"http://localhost:8000/uploads/clips/{clip_filename}",
            duration=duration,
            platform=platform
        )
        db.add(clip)
        db.commit()
        db.refresh(clip)
        
        return {
            "message": f"{platform} clip generated successfully", 
            "clip_id": clip.id,
            "clip_url": clip.s3_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clip generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))