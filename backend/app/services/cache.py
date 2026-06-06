"""
Simple in-memory cache service for frequently accessed data
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import asyncio

class CacheService:
    """
    Simple in-memory cache with TTL support.
    Suitable for dashboard statistics and other frequently accessed data.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now() < entry['expires_at']:
                    return entry['value']
                else:
                    # Remove expired entry
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 5 minutes)
        """
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl_seconds),
                'created_at': datetime.now()
            }
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern (simple prefix match).
        
        Args:
            pattern: Key prefix to match
            
        Returns:
            Number of keys deleted
        """
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def stats(self) -> Dict:
        """Get cache statistics."""
        async with self._lock:
            now = datetime.now()
            active = sum(1 for v in self._cache.values() if now < v['expires_at'])
            expired = len(self._cache) - active
            return {
                'total_keys': len(self._cache),
                'active_keys': active,
                'expired_keys': expired
            }


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
