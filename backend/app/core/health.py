"""
Advanced Health Check System
Provides comprehensive health monitoring for the application
"""
from typing import Dict, Any
import asyncio
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.cache import cache_manager


class HealthChecker:
    """Comprehensive health check manager"""
    
    @staticmethod
    async def check_database(db: AsyncSession) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            start_time = datetime.now()
            result = await db.execute(text("SELECT 1"))
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection": "ok"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
    
    @staticmethod
    async def check_cache() -> Dict[str, Any]:
        """Check Redis cache connectivity"""
        try:
            start_time = datetime.now()
            
            # Try to set and get a test value
            test_key = "health_check_test"
            test_value = "ok"
            
            await cache_manager.set(test_key, test_value, ttl=10)
            result = await cache_manager.get(test_key)
            await cache_manager.delete(test_key)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if result == test_value:
                return {
                    "status": "healthy",
                    "type": "redis" if cache_manager.use_redis else "memory",
                    "response_time_ms": round(response_time, 2)
                }
            else:
                return {
                    "status": "degraded",
                    "type": "memory",
                    "message": "Using fallback memory cache"
                }
                
        except Exception as e:
            return {
                "status": "degraded",
                "type": "memory",
                "error": str(e),
                "message": "Cache error, using memory fallback"
            }
    
    @staticmethod
    def check_disk_space() -> Dict[str, Any]:
        """Check disk space availability"""
        try:
            import shutil
            from app.config import settings
            
            usage = shutil.disk_usage(settings.UPLOAD_DIR)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            percent_used = (usage.used / usage.total) * 100
            
            status = "healthy"
            if percent_used > 90:
                status = "critical"
            elif percent_used > 80:
                status = "warning"
            
            return {
                "status": status,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent_used": round(percent_used, 2)
            }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    @staticmethod
    async def check_all(db: AsyncSession) -> Dict[str, Any]:
        """Perform all health checks"""
        checks = await asyncio.gather(
            HealthChecker.check_database(db),
            HealthChecker.check_cache(),
            return_exceptions=True
        )
        
        db_health = checks[0] if not isinstance(checks[0], Exception) else {
            "status": "error", "error": str(checks[0])
        }
        cache_health = checks[1] if not isinstance(checks[1], Exception) else {
            "status": "error", "error": str(checks[1])
        }
        disk_health = HealthChecker.check_disk_space()
        
        # Determine overall status
        statuses = [
            db_health.get("status"),
            cache_health.get("status"),
            disk_health.get("status")
        ]
        
        if "unhealthy" in statuses or "error" in statuses or "critical" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses or "warning" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": db_health,
                "cache": cache_health,
                "disk": disk_health
            }
        }


async def get_detailed_health(db: AsyncSession) -> Dict[str, Any]:
    """Get detailed health information"""
    return await HealthChecker.check_all(db)


async def get_simple_health() -> Dict[str, Any]:
    """Get simple health status for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
