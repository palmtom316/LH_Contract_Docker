"""Compatibility adapter for the application's single shared cache manager."""
from typing import Any, Optional, Dict

from app.core.cache import cache_manager

class CacheService:
    """Backward-compatible facade backed by Redis/CacheManager."""

    async def get(self, key: str) -> Optional[Any]:
        return await cache_manager.get(key)
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 5 minutes)
        """
        await cache_manager.set(key, value, ttl=ttl_seconds)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        existed = await cache_manager.get(key) is not None
        await cache_manager.delete(key)
        return existed
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        await cache_manager.clear_pattern("*")
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern (simple prefix match).
        
        Args:
            pattern: Key prefix to match
            
        Returns:
            Number of keys deleted
        """
        normalized_pattern = pattern if any(char in pattern for char in "*?") else f"{pattern}*"
        return await cache_manager.clear_pattern(normalized_pattern)
    
    async def stats(self) -> Dict:
        """Get cache statistics."""
        if cache_manager.use_redis and cache_manager.redis_client:
            total = len([key async for key in cache_manager.redis_client.scan_iter(match="*")])
        else:
            total = len(cache_manager.memory_cache)
        return {"total_keys": total, "active_keys": total, "expired_keys": 0}


# Global cache instance
cache = CacheService()


# Cache key generators for consistent key naming
def dashboard_cache_key() -> str:
    """Generate cache key for dashboard summary."""
    return "dashboard:summary"


def contract_count_cache_key(contract_type: str) -> str:
    """Generate cache key for contract count."""
    return f"contracts:{contract_type}:count"


def report_cache_key(report_type: str, **params) -> str:
    """Generate cache key for reports."""
    param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()) if v)
    return f"report:{report_type}:{param_str}" if param_str else f"report:{report_type}"
