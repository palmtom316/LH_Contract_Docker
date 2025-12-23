"""
Audit Log Service - 审计日志服务
"""
import json
from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.sql import func

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditAction:
    """Audit action constants"""
    # Auth
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    
    # CRUD
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    
    # Financial
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    
    # File
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"


class ResourceType:
    """Resource type constants"""
    USER = "用户"
    UPSTREAM_CONTRACT = "上游合同"
    DOWNSTREAM_CONTRACT = "下游合同"
    MANAGEMENT_CONTRACT = "管理合同"
    EXPENSE = "无合同费用"
    RECEIVABLE = "应收款"
    PAYABLE = "应付款"
    INVOICE = "挂账"
    PAYMENT = "付款"
    RECEIPT = "回款"
    SETTLEMENT = "结算"
    FILE = "文件"
    SYSTEM = "系统"
    ZERO_HOUR_LABOR = "零星用工"


async def create_audit_log(
    db: AsyncSession,
    user: Optional[User],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    description: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """Create an audit log entry"""
    log = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        description=description,
        old_values=json.dumps(old_values, ensure_ascii=False, default=str) if old_values else None,
        new_values=json.dumps(new_values, ensure_ascii=False, default=str) if new_values else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    await db.commit()
    return log


async def get_audit_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None
) -> dict:
    """Get paginated audit logs with filtering"""
    # Build query
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    
    conditions = []
    
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    
    if action:
        conditions.append(AuditLog.action == action)
    
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    
    if end_date:
        conditions.append(AuditLog.created_at <= f"{end_date} 23:59:59")
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        conditions.append(
            (AuditLog.username.ilike(keyword_filter)) |
            (AuditLog.resource_name.ilike(keyword_filter)) |
            (AuditLog.description.ilike(keyword_filter))
        )
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request"""
    # Check X-Forwarded-For header (for proxied requests)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request) -> Optional[str]:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "")[:500]
