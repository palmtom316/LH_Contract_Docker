"""
Application Configuration

All sensitive values should be set via environment variables.
See .env.example for configuration template.
"""
from pydantic_settings import BaseSettings
from typing import List
import os
import secrets

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """Application settings"""
    # Application
    APP_NAME: str = "LH Contract Management System"
    APP_VERSION: str = "1.1.0"  # Updated to V1.1
    DEBUG: bool = False  # Default to False for security
    
    # Database - MUST be set via environment variable in production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://lh_admin:LanHai2024Secure!@db:5432/lh_contract_db"
    )
    
    # Security - MUST be set via environment variable in production
    # Generate strong key: python -c "import secrets; print(secrets.token_urlsafe(64))"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(64))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2  # 2 hours (shortened for security)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh token
    
    # CORS - Whitelist of allowed origins
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # File Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "xlsx", "xls", "doc", "docx", "jpg", "jpeg", "png"]
    
    # Redis Cache (Optional - falls back to memory cache if not available)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "contracts"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "invoices"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "receipts"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "settlements"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "expenses"), exist_ok=True)
