"""
Authentication Router
Enhanced with rate limiting for security
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import List

from app.database import get_db
from app.models.user import User, UserRole, ROLE_DISPLAY_NAMES
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, RoleOption, RoleListResponse, RefreshTokenRequest
from app.services.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_refresh_token_with_db,
    verify_refresh_token_with_db,
    revoke_refresh_token,
    revoke_all_user_tokens,
    get_current_user,
    get_current_active_user
)
from app.core.permissions import get_user_permissions
from app.services.audit_service import create_audit_log, AuditAction, ResourceType, get_client_ip, get_user_agent
from app.config import settings
from app.core.rate_limit import limiter, RATE_LIMITS
from app.core.errors import AuthenticationError, PermissionDeniedError, DuplicateRecordError, ValidationError, ResourceNotFoundError, ErrorCode

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # ... existing register logic ...
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise DuplicateRecordError(
            resource_type="用户",
            field_name="username",
            field_value=user_data.username
        )
    
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise DuplicateRecordError(
            resource_type="用户",
            field_name="email",
            field_value=user_data.email
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Audit log for registration (usually implicit system action or self-registration)
    # If this is admin registering users, we might want current_user dependency. 
    # But for public registration, we leave user=new_user or None.
    # Assuming public registration for now or handle in separate admin user create.
    
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit(RATE_LIMITS["login"])  # 5 requests per minute for login
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """User login - get access token"""
    
    # Find user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError(
            message="用户名或密码错误",
            detail="请检查您的登录凭据"
        )
    
    if not user.is_active:
        raise PermissionDeniedError(
            message="用户已被禁用",
            detail="请联系管理员"
        )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    # Create audit log
    await create_audit_log(
        db=db,
        user=user,
        action=AuditAction.LOGIN,
        resource_type=ResourceType.SYSTEM,
        description=f"用户 {user.username} 登录系统",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Create access token and refresh token
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    refresh_token = await create_refresh_token_with_db(data=token_data, db=db)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        user=UserResponse.from_orm_with_permissions(user, get_user_permissions(user))
    )


@router.post("/login/json", response_model=Token)
@limiter.limit(RATE_LIMITS["login"])  # 5 requests per minute for login
async def login_json(
    request: Request,
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """User login - JSON version"""
    # Find user by username
    result = await db.execute(select(User).where(User.username == user_in.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise AuthenticationError(
            message="用户名或密码错误",
            detail="请检查您的登录凭据"
        )
    
    if not user.is_active:
        raise PermissionDeniedError(
            message="用户已被禁用",
            detail="请联系管理员"
        )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    # Create audit log
    await create_audit_log(
        db=db,
        user=user,
        action=AuditAction.LOGIN,
        resource_type=ResourceType.SYSTEM,
        description=f"用户 {user.username} 登录系统 (JSON)",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Create access token and refresh token
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    refresh_token = await create_refresh_token_with_db(data=token_data, db=db)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        user=UserResponse.from_orm_with_permissions(user, get_user_permissions(user))
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information with permissions"""
    permissions = get_user_permissions(current_user)
    return UserResponse.from_orm_with_permissions(current_user, permissions)



class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise ValidationError(
            message="原密码错误",
            field_errors={"old_password": "请输入正确的原密码"}
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.CHANGE_PASSWORD,
        resource_type=ResourceType.USER,
        description=f"用户 {current_user.username} 修改密码",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"message": "密码修改成功"}


@router.post("/init-admin")
async def init_admin(request: Request, db: AsyncSession = Depends(get_db)):
    """Initialize admin user (only works if no users exist)"""
    # Protect init in production: require token unless DEBUG
    if not settings.DEBUG:
        if not settings.INIT_ADMIN_TOKEN:
            raise PermissionDeniedError(
                message="未配置管理员初始化令牌",
                detail="请设置 INIT_ADMIN_TOKEN 环境变量后重试"
            )
        provided = request.headers.get("X-Init-Admin-Token", "")
        if provided != settings.INIT_ADMIN_TOKEN:
            raise PermissionDeniedError(
                message="初始化令牌无效",
                detail="缺少或错误的 X-Init-Admin-Token"
            )

    # Check if any users exist
    result = await db.execute(select(User))
    if result.first():
        raise ValidationError(
            message="系统已初始化",
            field_errors={"system": "无法再次创建管理员"}
        )
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@lanhai.com",
        hashed_password=get_password_hash("admin123"),
        full_name="系统管理员",
        role=UserRole.ADMIN,
        is_superuser=True,
        is_active=True
    )
    
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    
    return {
        "message": "管理员账户创建成功",
        "username": "admin",
        "default_password": "admin123",
        "note": "请立即修改默认密码"
    }


@router.get("/roles", response_model=RoleListResponse)
async def get_available_roles(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available roles for user management"""
    # Only admin can see all roles
    if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        raise PermissionDeniedError(
            message="只有管理员可以查看角色列表",
            detail="您的账户没有足够的权限"
        )
    
    roles = [
        RoleOption(value=role.value, label=ROLE_DISPLAY_NAMES.get(role, role.value))
        for role in UserRole
    ]
    return RoleListResponse(roles=roles)


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    Implements token rotation: old token is revoked, new token is issued.
    """
    # Verify the refresh token (with database revocation check)
    payload = await verify_refresh_token_with_db(token_request.refresh_token, db)
    if not payload:
        raise AuthenticationError(
            message="无效或已过期的刷新令牌",
            detail="请重新登录"
        )
    
    # Get user from token payload
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise AuthenticationError(
            message="无效的刷新令牌",
            detail="Token 数据异常"
        )
    
    # Fetch user from database to ensure they still exist and are active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise ResourceNotFoundError(resource_type="用户", resource_id=user_id)
    
    if not user.is_active:
        raise PermissionDeniedError(
            message="用户已被禁用",
            detail="请联系管理员"
        )
    
    # Revoke old refresh token (if it has JTI)
    old_jti = payload.get("jti")
    if old_jti:
        await revoke_refresh_token(old_jti, db)
    
    # Create new access token and rotated refresh token
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    new_refresh_token = await create_refresh_token_with_db(data=token_data, db=db)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,  # Rotated: new token issued
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm_with_permissions(user, get_user_permissions(user))
    )


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout user by revoking all their refresh tokens.
    This forces re-authentication on all devices.
    """
    revoked_count = await revoke_all_user_tokens(current_user.id, db)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.LOGOUT,
        resource_type=ResourceType.SYSTEM,
        description=f"用户 {current_user.username} 登出系统 (撤销 {revoked_count} 个令牌)",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"message": "登出成功", "revoked_tokens": revoked_count}
