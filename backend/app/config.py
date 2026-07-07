"""
Application Configuration

All sensitive values should be set via environment variables.
See .env.example for configuration template.
"""
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings
from typing import List
import hashlib
import os
import secrets
import tempfile
from urllib.parse import urlparse

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_SECRET_HASHES = {
    # SHA-256 hashes of historical/default credentials that must never be reused.
    "d51a695df7cb6e35e91ca8749cde10ec323a51881518f6cfc829bbf71d4c4f87",
    "40e9da8a3845c7eb0150de12b375909915b6325b3be00a2d056315da074ec386",
    "240be518fabd2724c9b51f4bb23a665a9809e51b432f30278d58189f8d6223f9",
    "452a4e2d1e58e0e61956387531a9d8a50ec3436444e40f8e3205fb49d136e82d",
    "1a3d6546ce705b341b48cb903dcd4551f5a50c5fc8917f369930d2052ab3fc9a",
}


def _is_forbidden_secret(value: str) -> bool:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() in FORBIDDEN_SECRET_HASHES


def _secret_parts(name: str, value: str) -> List[str]:
    parts = [value]
    if name.endswith("URL"):
        parsed = urlparse(value)
        if parsed.password:
            parts.append(parsed.password)
    return parts


class Settings(BaseSettings):
    """Application settings"""
    # Application
    APP_NAME: str = "LH Contract Management System"
    APP_VERSION: str = "1.7.1"
    DEBUG: bool = False  # Default to False for security
    
    # Database - MUST be set via environment variable
    DATABASE_URL: str = ""
    
    # Security - MUST be set via environment variable in production
    # Generate strong key: python -c "import secrets; print(secrets.token_urlsafe(64))"
    # In production, SECRET_KEY MUST be set as environment variable
    # In development, a warning will be logged if using default key
    SECRET_KEY: str = ""
    
    @model_validator(mode='after')
    def validate_security(self) -> 'Settings':
        """Reject missing or known placeholder credentials outside explicit dev mode."""
        if not self.DATABASE_URL and not self.DEBUG:
            raise ValueError("DATABASE_URL 环境变量在生产环境中必须设置")

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

        protected_values = {
            "DATABASE_URL": self.DATABASE_URL,
            "SECRET_KEY": self.SECRET_KEY,
            "MINIO_ACCESS_KEY": self.MINIO_ACCESS_KEY,
            "MINIO_SECRET_KEY": self.MINIO_SECRET_KEY,
            "INIT_ADMIN_TOKEN": self.INIT_ADMIN_TOKEN,
        }
        placeholder_marker = "CHANGE" + "_THIS"
        for name, value in protected_values.items():
            if value and placeholder_marker in value:
                raise ValueError(f"{name} 不能使用占位符")
            for part in _secret_parts(name, value):
                if part and _is_forbidden_secret(part):
                    raise ValueError(f"{name} 不能使用公开示例值或历史默认值")

        minio_values = [self.MINIO_ENDPOINT, self.MINIO_ACCESS_KEY, self.MINIO_SECRET_KEY]
        if any(minio_values) and not all(minio_values):
            raise ValueError("MINIO_ENDPOINT、MINIO_ACCESS_KEY、MINIO_SECRET_KEY 必须同时配置")

        legacy_bucket = os.getenv("MINIO_BUCKET_ACTIVE")
        if "MINIO_BUCKET_CONTRACTS" not in os.environ and legacy_bucket:
            self.MINIO_BUCKET_CONTRACTS = legacy_bucket

        upload_dir_abs = os.path.abspath(self.UPLOAD_DIR)
        backup_tmp_dir_abs = os.path.abspath(self.BACKUP_TMP_DIR)
        upload_dir_real = os.path.realpath(self.UPLOAD_DIR)
        backup_tmp_dir_real = os.path.realpath(self.BACKUP_TMP_DIR)
        if (
            backup_tmp_dir_abs == upload_dir_abs
            or backup_tmp_dir_abs.startswith(upload_dir_abs + os.sep)
            or backup_tmp_dir_real == upload_dir_real
            or backup_tmp_dir_real.startswith(upload_dir_real + os.sep)
        ):
            raise ValueError("BACKUP_TMP_DIR 不能位于 UPLOAD_DIR 之内")
        return self
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2  # 2 hours (shortened for security)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh token
    ENABLE_API_DOCS: bool = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
    
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
    
    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "")
    MINIO_ACCESS_KEY: str = Field(default_factory=lambda: os.getenv("MINIO_ROOT_USER", ""))
    MINIO_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("MINIO_ROOT_PASSWORD", ""))
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_BUCKET_CONTRACTS: str = Field(
        default="contracts-active",
        validation_alias=AliasChoices("MINIO_BUCKET_CONTRACTS", "MINIO_BUCKET_ACTIVE"),
    )
    
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
