"""
Report Caching Service
Provides caching for expensive report queries to improve performance
"""
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from app.core.cache import cache_manager

logger = logging.getLogger(__name__)

# Cache key prefixes
CACHE_PREFIX_DASHBOARD = "dashboard"
CACHE_PREFIX_REPORTS = "reports"
CACHE_PREFIX_CONTRACTS = "contracts"

# Cache TTL settings (in seconds)
CACHE_TTL_DASHBOARD = 300  # 5 minutes - Dashboard stats change frequently
CACHE_TTL_REPORTS = 600    # 10 minutes - Reports are more stable
CACHE_TTL_SUMMARY = 300    # 5 minutes - Contract summaries


def get_dashboard_cache_key(year: int, month: Optional[int] = None) -> str:
    """Generate cache key for dashboard data"""
    if month:
        return f"{CACHE_PREFIX_DASHBOARD}:stats:{year}:{month}"
    return f"{CACHE_PREFIX_DASHBOARD}:stats:{year}"


def get_report_cache_key(report_type: str, year: int, month: Optional[int] = None) -> str:
    """Generate cache key for report data"""
    if month:
        return f"{CACHE_PREFIX_REPORTS}:{report_type}:{year}:{month}"
    return f"{CACHE_PREFIX_REPORTS}:{report_type}:{year}"


async def get_cached_dashboard_stats(year: int, month: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Get cached dashboard statistics"""
    cache_key = get_dashboard_cache_key(year, month)
    data = await cache_manager.get(cache_key)
    if data:
        logger.debug(f"[CACHE] Dashboard stats cache HIT: {cache_key}")
    return data


async def set_cached_dashboard_stats(year: int, month: Optional[int], data: Dict[str, Any]) -> bool:
    """Cache dashboard statistics"""
    cache_key = get_dashboard_cache_key(year, month)
    success = await cache_manager.set(cache_key, data, ttl=CACHE_TTL_DASHBOARD)
    if success:
        logger.debug(f"[CACHE] Dashboard stats cached: {cache_key}")
    return success


async def get_cached_report(report_type: str, year: int, month: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Get cached report data"""
    cache_key = get_report_cache_key(report_type, year, month)
    data = await cache_manager.get(cache_key)
    if data:
        logger.debug(f"[CACHE] Report cache HIT: {cache_key}")
    return data


async def set_cached_report(report_type: str, year: int, month: Optional[int], data: Dict[str, Any]) -> bool:
    """Cache report data"""
    cache_key = get_report_cache_key(report_type, year, month)
    success = await cache_manager.set(cache_key, data, ttl=CACHE_TTL_REPORTS)
    if success:
        logger.debug(f"[CACHE] Report cached: {cache_key}")
    return success


async def invalidate_dashboard_cache(year: Optional[int] = None) -> int:
    """
    Invalidate dashboard cache.
    If year is provided, only invalidate that year's cache.
    Otherwise, invalidate all dashboard caches.
    """
    if year:
        pattern = f"{CACHE_PREFIX_DASHBOARD}:stats:{year}:*"
    else:
        pattern = f"{CACHE_PREFIX_DASHBOARD}:*"
    
    count = await cache_manager.clear_pattern(pattern)
    logger.info(f"[CACHE] Invalidated {count} dashboard cache entries")
    return count


async def invalidate_report_cache(report_type: Optional[str] = None, year: Optional[int] = None) -> int:
    """
    Invalidate report cache.
    Can filter by report_type and/or year.
    """
    if report_type and year:
        pattern = f"{CACHE_PREFIX_REPORTS}:{report_type}:{year}:*"
    elif report_type:
        pattern = f"{CACHE_PREFIX_REPORTS}:{report_type}:*"
    elif year:
        pattern = f"{CACHE_PREFIX_REPORTS}:*:{year}:*"
    else:
        pattern = f"{CACHE_PREFIX_REPORTS}:*"
    
    count = await cache_manager.clear_pattern(pattern)
    logger.info(f"[CACHE] Invalidated {count} report cache entries")
    return count


async def invalidate_all_report_caches() -> int:
    """Invalidate all report-related caches"""
    count = 0
    count += await cache_manager.clear_pattern(f"{CACHE_PREFIX_DASHBOARD}:*")
    count += await cache_manager.clear_pattern(f"{CACHE_PREFIX_REPORTS}:*")
    count += await cache_manager.clear_pattern(f"{CACHE_PREFIX_CONTRACTS}:*")
    logger.info(f"[CACHE] Invalidated {count} total cache entries")
    return count


# Decorator for caching report endpoints
def cached_report(report_type: str, ttl: int = CACHE_TTL_REPORTS):
    """
    Decorator for caching report endpoints.
    
    Usage:
        @cached_report("finance_trend", ttl=600)
        async def get_finance_trend(year: int, month: int = None, ...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, year: int = None, month: int = None, **kwargs):
            # Check cache first
            if year:
                cache_key = get_report_cache_key(report_type, year, month)
                cached_data = await cache_manager.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"[CACHE] Report endpoint HIT: {cache_key}")
                    return cached_data
            
            # Cache miss - execute function
            result = await func(*args, year=year, month=month, **kwargs)
            
            # Cache the result
            if year and result:
                await cache_manager.set(cache_key, result, ttl=ttl)
                logger.debug(f"[CACHE] Report endpoint cached: {cache_key}")
            
            return result
        
        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
