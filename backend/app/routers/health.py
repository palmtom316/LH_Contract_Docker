"""
Enhanced Health Check Endpoints
Provides detailed system health status for monitoring
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
import asyncio

from app.database import get_db
from app.core.cache import cache_manager

router = APIRouter()


async def check_database(db: AsyncSession) -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        start = asyncio.get_event_loop().time()
        await db.execute(text("SELECT 1"))
        latency = (asyncio.get_event_loop().time() - start) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)[:100]
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        if cache_manager.redis_client:
            start = asyncio.get_event_loop().time()
            await cache_manager.redis_client.ping()
            latency = (asyncio.get_event_loop().time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2)
            }
        else:
            return {
                "status": "degraded",
                "message": "Using memory cache"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)[:100]
        }


async def check_minio() -> Dict[str, Any]:
    """Check MinIO connectivity"""
    try:
        from app.core.minio import minio_client
        if minio_client:
            buckets = minio_client.list_buckets()
            return {
                "status": "healthy",
                "buckets": len(buckets)
            }
        else:
            return {
                "status": "not_configured",
                "message": "MinIO not configured"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)[:100]
        }


@router.get("/health/detailed")
async def health_check_detailed(db: AsyncSession = Depends(get_db)):
    """Detailed health check for all system components"""
    checks = {
        "database": await check_database(db),
        "redis": await check_redis(),
        "minio": await check_minio()
    }

    # Determine overall status
    statuses = [check["status"] for check in checks.values()]
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
        status_code = 200
    elif any(s == "unhealthy" for s in statuses):
        overall_status = "unhealthy"
        status_code = 503
    else:
        overall_status = "degraded"
        status_code = 200

    return {
        "status": overall_status,
        "checks": checks,
        "version": "1.5.0"
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe"""
    db_check = await check_database(db)

    if db_check["status"] == "healthy":
        return {"status": "ready"}
    else:
        return {"status": "not_ready"}, 503


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
