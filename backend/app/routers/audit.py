"""
Audit Log Router - 审计日志API
Refactored to use standardized AppException
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogListResponse
from app.services.auth import get_current_active_user
from app.core.permissions import require_roles
from app.services.audit_service import get_audit_logs
from app.core.errors import ValidationError, DatabaseError

router = APIRouter()


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated audit logs (Admin only)"""
    result = await get_audit_logs(
        db=db,
        page=page,
        page_size=page_size,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword
    )
    return result


@router.get("/actions")
async def get_action_types(
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Get available action types"""
    return {
        "actions": [
            {"value": "LOGIN", "label": "登录"},
            {"value": "LOGOUT", "label": "登出"},
            {"value": "CHANGE_PASSWORD", "label": "修改密码"},
            {"value": "CREATE", "label": "新增"},
            {"value": "UPDATE", "label": "修改"},
            {"value": "DELETE", "label": "删除"},
            {"value": "EXPORT", "label": "导出"},
            {"value": "UPLOAD", "label": "上传"},
            {"value": "DOWNLOAD", "label": "下载"},
        ]
    }


@router.get("/resource-types")
async def get_resource_types(
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Get available resource types"""
    return {
        "resource_types": [
            {"value": "用户", "label": "用户"},
            {"value": "上游合同", "label": "上游合同"},
            {"value": "下游合同", "label": "下游合同"},
            {"value": "管理合同", "label": "管理合同"},
            {"value": "无合同费用", "label": "无合同费用"},
            {"value": "应收款", "label": "应收款"},
            {"value": "应付款", "label": "应付款"},
            {"value": "挂账", "label": "挂账"},
            {"value": "付款", "label": "付款"},
            {"value": "回款", "label": "回款"},
            {"value": "结算", "label": "结算"},
            {"value": "文件", "label": "文件"},
            {"value": "系统", "label": "系统"},
        ]
    }


@router.delete("/cleanup")
async def delete_audit_logs_before_date(
    before_date: str = Query(..., description="Delete logs before this date (YYYY-MM-DD)"),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete all audit logs before specified date (Admin only)"""
    from datetime import datetime
    from sqlalchemy import delete
    from app.models.audit_log import AuditLog
    
    try:
        # Parse date
        cutoff_date = datetime.strptime(before_date, '%Y-%m-%d').date()
        
        # Delete logs before this date
        stmt = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 条审计日志",
            "deleted_count": deleted_count,
            "before_date": before_date
        }
    except ValueError:
        raise ValidationError(
            message="日期格式错误",
            field_errors={"before_date": "请使用 YYYY-MM-DD 格式"}
        )
    except Exception as e:
        raise DatabaseError(message="删除失败", detail=str(e))


@router.get("/statistics")
async def get_audit_statistics(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get audit log statistics (Admin only)"""
    from app.services.audit_archive_service import AuditLogArchiveService
    
    service = AuditLogArchiveService(db)
    return await service.get_log_statistics()


@router.post("/archive")
async def archive_old_logs(
    days: int = Query(90, ge=30, description="Archive logs older than this many days"),
    export_format: str = Query("json", description="Export format: json or csv"),
    delete_after_export: bool = Query(True, description="Delete logs after exporting"),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive old audit logs (Admin only).
    
    Exports logs to JSON/CSV and optionally deletes them from database.
    """
    from app.services.audit_archive_service import AuditLogArchiveService
    
    if export_format not in ["json", "csv"]:
        raise ValidationError(
            message="不支持的导出格式",
            field_errors={"export_format": "只支持 json 或 csv 格式"}
        )
    
    service = AuditLogArchiveService(db)
    result = await service.archive_old_logs(
        days=days,
        export_format=export_format,
        delete_after_export=delete_after_export
    )
    
    return result


@router.get("/archives")
async def list_archives(
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """List all archive files (Admin only)"""
    from app.services.audit_archive_service import AuditLogArchiveService, ARCHIVE_DIR
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Don't need DB for this operation, just list files
    archives = []
    if ARCHIVE_DIR.exists():
        for filepath in sorted(ARCHIVE_DIR.glob("audit_logs_archive_*"), reverse=True):
            if filepath.is_file():
                stat = filepath.stat()
                archives.append({
                    "filename": filepath.name,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return {"archives": archives, "total": len(archives)}

