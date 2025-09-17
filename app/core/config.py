from pydantic_settings import BaseSettings
from typing import List
import os
import cloudinary

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./quivio.db"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = 'dyq86hr38'
    CLOUDINARY_API_KEY: str = '689338187517471'
    CLOUDINARY_API_SECRET: str = 'WcIuDIupzD49hEDjO2DsBv5oDMk'
        
    # Email Configuration - Match your .env exactly
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_ENABLED: bool = False
    EMAIL_FROM_NAME: str = "Quivio"
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 1
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-add frontend URL to CORS for production
        if self.ENVIRONMENT == "production" and self.FRONTEND_URL:
            if self.FRONTEND_URL not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(self.FRONTEND_URL)

settings = Settings()

# Configure cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)