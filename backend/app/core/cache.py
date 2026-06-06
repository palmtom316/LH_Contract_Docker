"""
Redis Cache Manager for Performance Optimization
Provides caching functionality for frequently accessed data
"""
from typing import Optional, Any, Callable
from functools import wraps
import fnmatch
import json
import logging
import hashlib
from datetime import timedelta
import time

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from cachetools import TTLCache
    TTLCACHE_AVAILABLE = True
except ImportError:
    TTLCACHE_AVAILABLE = False
    TTLCache = None

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Async Redis cache manager with fallback to in-memory TTL cache"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        # Use TTLCache with 1000 max items and 5 minute default TTL
        if TTLCACHE_AVAILABLE:
            self.memory_cache = TTLCache(maxsize=1000, ttl=300)
        else:
            # Fallback to dict with manual TTL tracking
            self.memory_cache = {}
            self.memory_cache_expiry = {}  # Track expiry times
        self.use_redis = REDIS_AVAILABLE
        
    async def connect(self):
        """Connect to Redis server"""
        if not REDIS_AVAILABLE:
            logger.warning("[CACHE] Redis not available, using in-memory cache")
            return
        
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            logger.info(f"[CACHE] Connected to Redis: {redis_url}")
        except Exception as e:
            logger.warning(f"[CACHE] Failed to connect to Redis: {e}, falling back to memory cache")
            self.use_redis = False
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("[CACHE] Redis connection closed")
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function name and arguments"""
        # Create a unique key based on arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Fallback to memory cache with TTL support
                if TTLCACHE_AVAILABLE:
                    # TTLCache handles expiry automatically
                    return self.memory_cache.get(key)
                else:
                    # Manual expiry check
                    expiry = self.memory_cache_expiry.get(key, 0)
                    if time.time() > expiry:
                        # Expired - remove and return None
                        self.memory_cache.pop(key, None)
                        self.memory_cache_expiry.pop(key, None)
                        return None
                    return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"[CACHE] Error getting key {key}: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (seconds)"""
        try:
            json_value = json.dumps(value, default=str)
            
            if self.use_redis and self.redis_client:
                await self.redis_client.setex(key, ttl, json_value)
            else:
                # Fallback to memory cache with TTL
                if TTLCACHE_AVAILABLE:
                    # TTLCache uses its configured TTL, but we can't set per-key TTL
                    # For per-key TTL, we'd need a different approach
                    self.memory_cache[key] = json.loads(json_value)
                else:
                    # Manual TTL tracking
                    self.memory_cache[key] = json.loads(json_value)
                    self.memory_cache_expiry[key] = time.time() + ttl
            
            return True
        except Exception as e:
            logger.error(f"[CACHE] Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"[CACHE] Error deleting key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if self.use_redis and self.redis_client:
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self.redis_client.delete(*keys)
                return len(keys)
            else:
                # Clear memory cache keys matching pattern (glob-style: *, ?)
                keys_to_delete = [k for k in self.memory_cache.keys() if fnmatch.fnmatchcase(k, pattern)]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return len(keys_to_delete)
        except Exception as e:
            logger.error(f"[CACHE] Error clearing pattern {pattern}: {e}")
            return 0
    
    def cached(self, ttl: int = 300, key_prefix: Optional[str] = None):
        """
        Decorator for caching function results
        
        Args:
            ttl: Time to live in seconds (default: 5 minutes)
            key_prefix: Custom key prefix (default: function name)
        
        Usage:
            @cache_manager.cached(ttl=600)
            async def get_expensive_data(param1, param2):
                # Expensive operation
                return result
        """
        def decorator(func: Callable):
            prefix = key_prefix or func.__name__
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._make_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"[CACHE] HIT: {cache_key}")
                    return cached_value
                
                # Cache miss - call original function
                logger.debug(f"[CACHE] MISS: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.set(cache_key, result, ttl=ttl)
                
                return result
            
            return wrapper
        return decorator


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def init_cache():
    """Initialize cache connection"""
    await cache_manager.connect()


async def close_cache():
    """Close cache connection"""
    await cache_manager.close()


async def clear_cache(pattern: str = "*"):
    """Clear cache by pattern"""
    count = await cache_manager.clear_pattern(pattern)
    logger.info(f"[CACHE] Cleared {count} keys matching pattern: {pattern}")
    return count
