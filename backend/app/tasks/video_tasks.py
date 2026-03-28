from celery import Celery
from sqlalchemy.orm import Session
import ffmpeg
import whisper
import numpy as np
from app.database import SessionLocal
from app import models
from app.utils.storage import download_from_s3, upload_to_s3
import tempfile
import os

celery = Celery('tasks', broker='redis://redis:6379/0')

@celery.task
def process_video(video_id: int):
    db = SessionLocal()
    try:
        # Update video status
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        video.status = "processing"
        video.processing_progress = 10
        db.commit()
        
        # Download video from S3
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            video_path = tmp_file.name
            download_from_s3(video.s3_key, video_path)
        
        # Get video duration
        probe = ffmpeg.probe(video_path)
        video.duration = float(probe['format']['duration'])
        video.processing_progress = 20
        db.commit()
        
        # Extract audio for transcription
        audio_path = video_path.replace('.mp4', '.wav')
        ffmpeg.input(video_path).output(audio_path, acodec='pcm_s16le', ac=1, ar='16k').run(overwrite_output=True)
        
        # Transcribe with Whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        
        # Save transcription
        transcription = models.Transcription(
            video_id=video_id,
            text=result['text'],
            segments=result['segments'],
            language=result['language']
        )
        db.add(transcription)
        video.processing_progress = 40
        db.commit()
        
        # Detect scenes and key moments
        scenes = detect_scenes(video_path)
        video.processing_progress = 60
        db.commit()
        
        # Generate clips for different platforms
        generate_clips(video_id, video_path, scenes, db)
        
        # Update video status
        video.status = "completed"
        video.processing_progress = 100
        db.commit()
        
        # Cleanup temp files
        os.unlink(video_path)
        os.unlink(audio_path)
        
    except Exception as e:
        video.status = "failed"
        video.processing_progress = 0
        db.commit()
        raise e
    finally:
        db.close()

def detect_scenes(video_path):
    """Detect scene changes in video"""
    probe = ffmpeg.probe(video_path, v='error', select_streams='v:0', show_entries='frame=pkt_pts_time,scene_score')
    scenes = []
    
    # Simple scene detection based on frame differences
    # You can implement more sophisticated detection here
    
    return scenes

def generate_clips(video_id, video_path, scenes, db):
    """Generate short clips from detected scenes"""
    # Implementation for clip generation
    # This would create clips for different platforms (9:16 aspect ratio)
    pass