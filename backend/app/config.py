from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:Ubo%401234@localhost/clipforge"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "clipforge-ai"
    AWS_REGION: str = "us-east-1"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # CORS - handle as comma-separated string from .env
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/quicktime", "video/mpeg", "video/webm"]
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "CORS_ORIGINS":
                # Parse comma-separated string into list
                return [origin.strip() for origin in raw_val.split(",")]
            return raw_val

settings = Settings()