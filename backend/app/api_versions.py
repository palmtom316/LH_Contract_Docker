"""
API Version Management
Supports multiple API versions for backward compatibility
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# V1 Router (current)
v1_router = APIRouter()

# V2 Router (future)
v2_router = APIRouter()


@v1_router.get("/version")
async def get_v1_version():
    """Get API v1 version info"""
    return {
        "version": "1.0",
        "status": "stable",
        "deprecated": False
    }


@v2_router.get("/version")
async def get_v2_version():
    """Get API v2 version info"""
    return {
        "version": "2.0",
        "status": "beta",
        "deprecated": False
    }


# Version deprecation middleware
async def version_deprecation_middleware(request: Request, call_next):
    """Add deprecation warnings to old API versions"""
    response = await call_next(request)

    # Add deprecation header for v1 if needed
    if request.url.path.startswith("/api/v1"):
        # Uncomment when v1 is deprecated
        # response.headers["X-API-Deprecated"] = "true"
        # response.headers["X-API-Sunset"] = "2027-01-01"
        pass

    return response
