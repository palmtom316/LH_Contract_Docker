"""
Audit Log Router - 审计日志API
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
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
