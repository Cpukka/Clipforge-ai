from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="creator")  # admin, creator, viewer
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = relationship("Video", back_populates="user")
    clips = relationship("Clip", back_populates="user")

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    description = Column(String)
    filename = Column(String)
    file_size = Column(Integer)
    duration = Column(Float)
    s3_key = Column(String)
    s3_url = Column(String)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    clips = relationship("Clip", back_populates="original_video")
    transcription = relationship("Transcription", back_populates="video", uselist=False)

class Clip(Base):
    __tablename__ = "clips"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    title = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    s3_key = Column(String)
    s3_url = Column(String)
    thumbnail_url = Column(String)
    duration = Column(Float)
    platform = Column(String)  # tiktok, instagram, youtube
    views = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="clips")
    original_video = relationship("Video", back_populates="clips")
    captions = relationship("Caption", back_populates="clip")

class Transcription(Base):
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), unique=True)
    text = Column(String)
    segments = Column(JSON)  # Store timestamped segments
    language = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="transcription")

class Caption(Base):
    __tablename__ = "captions"
    
    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id"))
    content = Column(String)  # AI-generated caption
    hashtags = Column(JSON)  # Array of hashtags
    title = Column(String)  # AI-generated title
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clip = relationship("Clip", back_populates="captions")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    job_type = Column(String)  # transcription, clip_generation, subtitle_burning
    status = Column(String, default="queued")  # queued, processing, completed, failed
    progress = Column(Integer, default=0)
    error_message = Column(String)
    celery_task_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)