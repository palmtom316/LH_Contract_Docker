"""
User Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db
from app.models.user import User, UserRole, ROLE_DISPLAY_NAMES
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.auth import (
    get_password_hash,
    get_current_active_user,
)
from app.core.permissions import Permission, require_permission, require_roles, get_user_permissions

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get list of users (Admin only)"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    
    # Return with permissions
    return [
        UserResponse.from_orm_with_permissions(u, get_user_permissions(u))
        for u in users
    ]


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
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    # Check if email exists (only if email is provided)
    if user_in.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="邮箱已被注册"
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
        raise HTTPException(status_code=403, detail="权限不足")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
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
        raise HTTPException(status_code=403, detail="权限不足")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    # Update fields
    if user_in.email is not None:
        # Check email uniqueness if changed (only for non-empty email)
        if user_in.email and user_in.email != user.email:
            email_check = await db.execute(select(User).where(User.email == user_in.email))
            if email_check.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="邮箱已被占用")
        user.email = user_in.email if user_in.email else None
        
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
        
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
    """Delete (deactivate) user"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户已删除"}


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100)


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
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "密码重置成功"}

