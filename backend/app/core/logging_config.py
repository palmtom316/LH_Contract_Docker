import logging
import sys
from pathlib import Path
from app.config import settings

# Create logs directory if it doesn't exist
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s", 
            # In a real app, use python-json-logger or similar for true JSON
        },
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "error_file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
            "level": "ERROR",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG" if settings.DEBUG else "INFO",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "uvicorn.error": {
            "handlers": ["console", "error_file"],
            "level": "INFO",
            "propagate": False
        },
        "fastapi": {
            "handlers": ["console"],
            "level": "INFO", 
        },
    },
    "root": {
        "handlers": ["console", "file", "error_file"],
        "level": "INFO",
    },
}

def setup_logging():
    """Configure logging based on settings"""
    logging.config.dictConfig(LOGGING_CONFIG)
