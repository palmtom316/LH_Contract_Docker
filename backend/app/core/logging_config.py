"""
Enhanced Logging Configuration for LH Contract Management System

Features:
- Sensitive data filtering (passwords, tokens, credentials)
- Request ID tracking across async calls
- File rotation with retention
- JSON format option for log aggregation
"""
import logging
import logging.config
import os
import sys
import re
import uuid
from pathlib import Path
from contextvars import ContextVar
from app.config import settings

# Get the project root directory (backend/)
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)

# Request ID context variable for tracking requests across async calls
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class SensitiveDataFilter(logging.Filter):
    """
    Filter to mask sensitive data in logs.
    
    Enhanced Security Features:
    - Masks passwords, tokens, and API keys
    - Partial masking for emails and phone numbers
    - Credit card number detection
    - Secret key protection
    - Database URL credential masking
    """
    
    SENSITIVE_PATTERNS = [
        # Password patterns
        (re.compile(r'("password"\s*:\s*")[^"]+(")'), r'\1***REDACTED***\2'),
        (re.compile(r'(password["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(old_password["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(new_password["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(hashed_password["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***REDACTED***'),
        
        # Token patterns  
        (re.compile(r'("token"\s*:\s*")[^"]+(")'), r'\1***TOKEN***\2'),
        (re.compile(r'("access_token"\s*:\s*")[^"]+(")'), r'\1***TOKEN***\2'),
        (re.compile(r'("refresh_token"\s*:\s*")[^"]+(")'), r'\1***TOKEN***\2'),
        (re.compile(r'(token["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***TOKEN***'),
        (re.compile(r'(Bearer\s+)[A-Za-z0-9_.-]+', re.IGNORECASE), r'\1***TOKEN***'),
        
        # Authorization header
        (re.compile(r'(Authorization["\s:=]+Bearer\s+)[A-Za-z0-9_.-]+', re.IGNORECASE), r'\1***TOKEN***'),
        (re.compile(r'(Authorization["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***REDACTED***'),
        
        # API Keys and Secrets
        (re.compile(r'(api[_-]?key["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***API_KEY***'),
        (re.compile(r'(secret[_-]?key["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***SECRET***'),
        (re.compile(r'(SECRET_KEY["\s:=]+)[^\s,}"\']+', re.IGNORECASE), r'\1***SECRET***'),
        
        # Database URLs with credentials
        (re.compile(r'(postgresql://[^:]+:)[^@]+(@)', re.IGNORECASE), r'\1***PASSWORD***\2'),
        (re.compile(r'(mysql://[^:]+:)[^@]+(@)', re.IGNORECASE), r'\1***PASSWORD***\2'),
        (re.compile(r'(redis://:[^@]+)(@)', re.IGNORECASE), r'redis://***PASSWORD***\2'),
        
        # Credit card numbers (basic pattern)
        (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'), '****-****-****-****'),
        
        # Social Security Numbers (SSN format)
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '***-**-****'),
        
        # Email addresses (partial masking)
        (re.compile(r'([a-zA-Z0-9._%+-]{1,3})[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-]+)'), r'\1***@\2'),
        
        # Phone numbers (China format)
        (re.compile(r'\b(1[3-9]\d)\d{4}(\d{4})\b'), r'\1****\2'),
        
        # ID card numbers (China format - 18 digits)
        (re.compile(r'\b(\d{6})\d{8}(\d{4})\b'), r'\1********\2'),
    ]
    
    def filter(self, record):
        """Filter sensitive data from log messages"""
        try:
            message = record.getMessage()
            
            # Apply all sensitive patterns
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                message = pattern.sub(replacement, message)
            
            # Update the record message
            record.msg = message
            record.args = ()  # Clear args to prevent double formatting
        except Exception:
            # Don't let logging errors crash the application
            pass
        
        return True


class RequestIdFilter(logging.Filter):
    """Add request ID to log records"""
    
    def filter(self, record):
        record.request_id = request_id_var.get('NO_REQUEST_ID')
        return True


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s", 
            # In a real app, use python-json-logger or similar for true JSON
        },
    },
    "filters": {
        "sensitive_filter": {
            "()": SensitiveDataFilter,
        },
        "request_id_filter": {
            "()": RequestIdFilter,
        },
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "filters": ["sensitive_filter", "request_id_filter"],
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'default',
            'filters': ["sensitive_filter", "request_id_filter"],
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOG_DIR / 'error.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'default',
            'filters': ["sensitive_filter", "request_id_filter"],
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


# Request ID Middleware for FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or get request ID from header
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        
        # Set in context variable for logging
        request_id_var.set(request_id)
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id
        
        return response
