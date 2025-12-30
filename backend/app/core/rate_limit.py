"""
Rate Limiting Module for API Security
Implements rate limiting using slowapi with Redis or in-memory backend

This module provides:
1. Global rate limiting for all API endpoints
2. Stricter limits for authentication-related endpoints
3. IP-based rate limiting
"""
import logging
from typing import Callable, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Check if slowapi is available
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    logger.warning("slowapi not installed - rate limiting will be disabled")


def get_client_ip(request) -> str:
    """
    Get the real client IP address from request.
    Handles X-Forwarded-For header for requests behind proxy/load balancer.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Also check X-Real-IP (used by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"


# Rate limit configuration
RATE_LIMITS = {
    # Default limits (requests per time period)
    "default": "100/minute",
    
    # Authentication endpoints - stricter limits
    "login": "5/minute",
    "register": "3/minute",
    "password_reset": "3/minute",
    
    # Sensitive operations
    "export": "10/minute",
    "import": "5/minute",
    "delete": "20/minute",
}


if SLOWAPI_AVAILABLE:
    # Create limiter with IP-based key function
    limiter = Limiter(
        key_func=get_client_ip,
        default_limits=[RATE_LIMITS["default"]],
        # Use in-memory storage by default
        # For production with multiple workers, configure Redis:
        # storage_uri="redis://redis:6379/1"
    )
    
    def setup_rate_limiting(app):
        """
        Setup rate limiting middleware for FastAPI application.
        
        Args:
            app: FastAPI application instance
        """
        # Add limiter to app state
        app.state.limiter = limiter
        
        # Add exception handler for rate limit exceeded
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # Add middleware
        app.add_middleware(SlowAPIMiddleware)
        
        logger.info("✅ Rate limiting enabled with slowapi")
        logger.info(f"   Default limit: {RATE_LIMITS['default']}")
        logger.info(f"   Login limit: {RATE_LIMITS['login']}")
else:
    # Mock limiter when slowapi is not available
    class MockLimiter:
        """Mock limiter that does nothing when slowapi is not installed"""
        def __init__(self, *args, **kwargs):
            pass
        
        def limit(self, limit_value: str = "", **kwargs) -> Callable:
            """Decorator that does nothing"""
            def decorator(func: Callable) -> Callable:
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    return await func(*args, **kwargs)
                return wrapper
            return decorator
        
        def shared_limit(self, limit_value: str = "", **kwargs) -> Callable:
            """Decorator that does nothing"""
            return self.limit(limit_value)
        
        def exempt(self, func: Callable) -> Callable:
            """Mark a route as exempt from rate limiting"""
            return func
    
    limiter = MockLimiter()
    
    def setup_rate_limiting(app):
        """No-op when slowapi is not available"""
        logger.warning("⚠️ Rate limiting disabled - install slowapi to enable")


# Convenience decorators for common rate limits
def rate_limit_login(func):
    """Apply strict rate limit for login endpoints"""
    return limiter.limit(RATE_LIMITS["login"])(func)


def rate_limit_sensitive(func):
    """Apply rate limit for sensitive operations"""
    return limiter.limit(RATE_LIMITS["delete"])(func)


def rate_limit_export(func):
    """Apply rate limit for export operations"""
    return limiter.limit(RATE_LIMITS["export"])(func)
