from celery import Celery
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.tasks.video_processor import VideoProcessor
import os
import tempfile
import uuid
import logging

logger = logging.getLogger(__name__)

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task(bind=True)
def process_video_for_clips(self, video_id: int):
    """Main task to process video and generate clips for social media"""
    db = SessionLocal()
    
    try:
        # Get video
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not video:
            logger.error(f"Video {video_id} not found")
            return
        
        logger.info(f"Processing video {video_id}: {video.title}")
        
        # Create processing job
        job = models.ProcessingJob(
            video_id=video_id,
            job_type="clip_generation",
            status="processing",
            celery_task_id=self.request.id
        )
        db.add(job)
        db.commit()
        
        # Initialize processor
        processor = VideoProcessor()
        
        # Download video to temp file
        local_path = None
        if video.s3_url and video.s3_url.startswith('http://localhost'):
            # Local file
            filename = video.s3_url.split("/")[-1]
            local_path = f"uploads/{filename}"
        else:
            # Would download from S3 here
            logger.warning("S3 download not implemented")
            job.status = "failed"
            job.error_message = "S3 download not implemented"
            db.commit()
            return
        
        if not os.path.exists(local_path):
            logger.error(f"Video file not found: {local_path}")
            job.status = "failed"
            job.error_message = f"Video file not found: {local_path}"
            db.commit()
            return
        
        # Get video info
        info = processor.get_video_info(local_path)
        logger.info(f"Video info: {info}")
        
        # Transcribe audio
        logger.info("Transcribing audio...")
        transcription = processor.extract_transcription(local_path)
        
        # Save transcription to database
        db_transcription = models.Transcription(
            video_id=video_id,
            text=transcription["text"],
            segments=transcription["segments"],
            language=transcription["language"]
        )
        db.add(db_transcription)
        db.commit()
        
        # Detect key moments
        logger.info("Detecting key moments...")
        key_moments = processor.detect_key_moments(local_path, transcription)
        
        # Generate clips for each platform
        platforms = ["tiktok", "instagram", "youtube"]
        generated_clips = []
        
        for moment in key_moments[:3]:  # Generate top 3 moments
            start = moment["start"]
            end = min(moment["end"] + 5, info["duration"])  # Add 5 seconds buffer
            
            for platform in platforms:
                # Generate unique filename
                clip_filename = f"{uuid.uuid4()}.mp4"
                clip_path = f"uploads/clips/{clip_filename}"
                os.makedirs("uploads/clips", exist_ok=True)
                
                # Generate clip
                success = processor.generate_clip(
                    local_path, start, end, clip_path, platform
                )
                
                if success:
                    # Create clip record
                    clip = models.Clip(
                        user_id=video.user_id,
                        video_id=video_id,
                        title=f"{video.title} - {moment['text'][:50]}",
                        start_time=start,
                        end_time=end,
                        s3_key=f"clips/{clip_filename}",
                        s3_url=f"http://localhost:8000/uploads/clips/{clip_filename}",
                        duration=end - start,
                        platform=platform
                    )
                    db.add(clip)
                    generated_clips.append(clip)
                    logger.info(f"Generated {platform} clip: {clip_filename}")
        
        db.commit()

        if len(generated_clips) == 0:
            logger.warning(f"No clips generated for video {video_id}, falling back to no key moments or conversion failure")
            job.status = "failed"
            job.error_message = "No clips generated"
        else:
            # Update job status
            job.status = "completed"
            job.progress = 100

        db.commit()
        
        logger.info(f"✅ Generated {len(generated_clips)} clips for video {video_id}")
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise e
    finally:
        db.close()

# Alias for backward compatibility
process_video = process_video_for_clips