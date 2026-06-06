"""
Reports Router Module
Aggregates all report-related sub-routers for better code organization.

Original: reports.py (1569 lines)
Now split into:
- summary.py: Contract summaries, finance trends, AR/AP stats (5 endpoints)
- exports.py: Excel export endpoints (13 endpoints)
"""
from fastapi import APIRouter

from .summary import router as summary_router
from .exports import router as exports_router

router = APIRouter()

# Include all sub-routers
router.include_router(summary_router)
router.include_router(exports_router)

# Re-export for backward compatibility
__all__ = ["router"]
