"""
User Management Router
Refactored to use standardized AppException
"""
from fastapi import APIRouter, Depends, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
import logging

from app.database import get_db
from app.models.user import User, UserRole, ROLE_DISPLAY_NAMES
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.auth import (
    get_password_hash,
    get_current_active_user,
)
from app.core.permissions import Permission, require_permission, require_roles, get_user_permissions
from app.core.errors import (
    AppException, ErrorCode, 
    ResourceNotFoundError, 
    PermissionDeniedError, 
    DuplicateRecordError,
    DatabaseError,
    ValidationError
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get list of users (Admin only)"""
    try:
        result = await db.execute(select(User).offset(skip).limit(limit))
        users = result.scalars().all()
        
        # Return with permissions - handle errors for each user
        user_responses = []
        for u in users:
            try:
                user_responses.append(
                    UserResponse.from_orm_with_permissions(u, get_user_permissions(u))
                )
            except Exception as e:
                # If individual user fails, log and skip
                logger.warning("Failed to build permission-rich user response for %s", u.username, exc_info=e)
                # Add basic response without permissions as fallback
                user_responses.append(UserResponse(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    full_name=u.full_name,
                    role=u.role,
                    role_display=ROLE_DISPLAY_NAMES.get(u.role, str(u.role)),
                    is_active=u.is_active,
                    is_superuser=u.is_superuser,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                    last_login=u.last_login,
                    permissions=[]
                ))
        return user_responses
    except Exception as e:
        logger.exception("Error fetching users")
        raise DatabaseError(message="获取用户列表失败", detail=str(e))


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (Admin only)"""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise DuplicateRecordError(
            resource_type="用户",
            field_name="用户名",
            field_value=user_in.username
        )
    
    # Check if email exists (only if email is provided)
    if user_in.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise DuplicateRecordError(
                resource_type="用户",
                field_name="邮箱",
                field_value=user_in.email
            )
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm_with_permissions(user, get_user_permissions(user))


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific user details"""
    # Allow users to read their own profile, otherwise require admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise PermissionDeniedError(detail="您只能查看自己的用户信息")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(resource_type="用户", resource_id=user_id)
    
    return UserResponse.from_orm_with_permissions(user, get_user_permissions(user))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user"""
    # Check permissions - users can update their own profile (limited fields), admin can update all
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_superuser
    
    if current_user.id != user_id and not is_admin:
        raise PermissionDeniedError(detail="您只能修改自己的用户信息")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(resource_type="用户", resource_id=user_id)
        
        
    # Update fields - Use model_dump to check which fields were explicitly set
    update_data = user_in.model_dump(exclude_unset=True)
    
    if 'email' in update_data:
        # Email was explicitly provided (could be string, empty string, or None)
        new_email = update_data['email']
        # Check email uniqueness if changed (only for non-empty email)
        if new_email and new_email != user.email:
            email_check = await db.execute(select(User).where(User.email == new_email))
            if email_check.scalar_one_or_none():
                raise DuplicateRecordError(
                    resource_type="用户",
                    field_name="邮箱",
                    field_value=new_email
                )
        # Set to new value (could be None to clear it)
        user.email = new_email if new_email else None
        
    if 'full_name' in update_data:
        user.full_name = update_data['full_name']
        
    # Only Admin can update roles and active status
    if is_admin:
        if user_in.role is not None:
            user.role = user_in.role
        if user_in.is_active is not None:
            user.is_active = user_in.is_active
            
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm_with_permissions(user, get_user_permissions(user))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Hard-delete a user (Admin only).

    Users with linked business data (contracts, finance records) cannot be deleted
    and must be disabled via PUT /{user_id} with is_active=false instead. Audit
    logs survive the delete with user_id cleared (ON DELETE SET NULL) but keep
    the username snapshot captured at log creation time.
    """
    if current_user.id == user_id:
        raise ValidationError(
            message="不能删除当前登录用户",
            field_errors={"user_id": "不能删除自己的账户"}
        )
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(resource_type="用户", resource_id=user_id)
        
    try:
        await db.delete(user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppException(
            error_code=ErrorCode.CONSTRAINT_VIOLATION,
            message="无法删除该用户",
            detail="该用户已关联业务数据（如创建了合同或财务记录）。为保持数据完整性，请将其状态修改为 [禁用] 即可。",
            status_code=400
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error deleting user %s", user_id)
        raise DatabaseError(message="数据库操作失败", detail="请重试或联系管理员")
    
    return {"message": "用户已删除"}


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=72)


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: ResetPasswordRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Reset user password (Admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(resource_type="用户", resource_id=user_id)
    
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "密码重置成功"}
