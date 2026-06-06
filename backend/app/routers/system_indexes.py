"""
System Management Endpoint for Database Indexes
Add this to system router to apply indexes via API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.models.user import User
from app.services.auth import get_current_active_user
from app.core.errors import PermissionDeniedError
from app.core.db_indexes import SQL_SCRIPT

router = APIRouter()


@router.post("/indexes/apply")
async def apply_performance_indexes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply performance indexes to database (Admin only)"""
    if not current_user.is_superuser:
        raise PermissionDeniedError(detail="需要超级管理员权限")
    statements = [
        s.strip()
        for s in SQL_SCRIPT.split(';')
        if s.strip() and not s.strip().startswith('--') and len(s.strip()) > 10
    ]

    success_count = 0
    error_count = 0
    errors = []

    for stmt in statements:
        try:
            await db.execute(text(stmt))
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(str(e)[:200])

    await db.commit()

    return {
        "success": success_count,
        "errors": error_count,
        "error_details": errors[:5],  # Return first 5 errors
        "message": f"Applied {success_count} indexes, {error_count} errors"
    }
