"""
Application Configuration

All sensitive values should be set via environment variables.
See .env.example for configuration template.
"""
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from typing import List
import os
import secrets
import tempfile

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """Application settings"""
    # Application
    APP_NAME: str = "LH Contract Management System"
    APP_VERSION: str = "1.6.2"  # Updated to V1.6.2
    DEBUG: bool = False  # Default to False for security
    
    # Database - MUST be set via environment variable in production
    # Development default uses placeholder credentials (NOT for production!)
    DATABASE_URL: str = "postgresql+asyncpg://lh_admin:dev_password_change_me@db:5432/lh_contract_db"
    
    # Security - MUST be set via environment variable in production
    # Generate strong key: python -c "import secrets; print(secrets.token_urlsafe(64))"
    # In production, SECRET_KEY MUST be set as environment variable
    # In development, a warning will be logged if using default key
    SECRET_KEY: str = ""
    
    @model_validator(mode='after')
    def validate_security(self) -> 'Settings':
        """Ensure SECRET_KEY is set in production"""
        if not self.SECRET_KEY:
            if not self.DEBUG:
                raise ValueError(
                    "SECRET_KEY 环境变量在生产环境中必须设置! "
                    "使用以下命令生成: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            else:
                import logging
                logging.warning(
                    "⚠️ 使用开发模式默认 SECRET_KEY，请勿在生产环境使用！"
                )
                self.SECRET_KEY = "DEV_ONLY_KEY_DO_NOT_USE_IN_PRODUCTION_abc123xyz789"
        return self
    
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
    BACKUP_TMP_DIR: str = os.getenv(
        "BACKUP_TMP_DIR",
        os.path.join(tempfile.gettempdir(), "lh_contract_backups")
    )
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "xlsx", "xls", "doc", "docx", "jpg", "jpeg", "png"]
    ALLOW_QUERY_TOKEN: bool = os.getenv("ALLOW_QUERY_TOKEN", "false").lower() == "true"
    
    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_BUCKET_CONTRACTS: str = os.getenv("MINIO_BUCKET_CONTRACTS", "contracts-active")
    
    # Redis Cache (Optional - falls back to memory cache if not available)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    # Admin initialization (production should require a token)
    INIT_ADMIN_TOKEN: str = os.getenv("INIT_ADMIN_TOKEN", "")

    # Trusted proxy IPs for client IP resolution (comma-separated). Use "*" to trust all.
    TRUSTED_PROXIES: str = os.getenv("TRUSTED_PROXIES", "")

    @property
    def trusted_proxies_list(self) -> List[str]:
        """Parse TRUSTED_PROXIES into a list"""
        return [ip.strip() for ip in self.TRUSTED_PROXIES.split(",") if ip.strip()]
    
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
os.makedirs(settings.BACKUP_TMP_DIR, exist_ok=True)
