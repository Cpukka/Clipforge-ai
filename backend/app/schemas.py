from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Video schemas
class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    user_id: int
    filename: str
    file_size: int
    duration: Optional[float]
    s3_url: str
    status: str
    processing_progress: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Clip schemas
class ClipBase(BaseModel):
    title: str
    start_time: float
    end_time: float
    platform: str

class ClipCreate(ClipBase):
    video_id: int

class ClipResponse(ClipBase):
    id: int
    user_id: int
    video_id: int
    s3_url: str
    thumbnail_url: Optional[str]
    duration: float
    views: int
    downloads: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Caption schemas
class CaptionResponse(BaseModel):
    id: int
    clip_id: int
    content: str
    hashtags: List[str]
    title: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Processing job schemas
class ProcessingJobResponse(BaseModel):
    id: int
    video_id: int
    job_type: str
    status: str
    progress: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True