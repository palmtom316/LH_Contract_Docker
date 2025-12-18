"""
Authentication Service - Password hashing and JWT handling
Enhanced with security improvements
"""
from datetime import datetime, timedelta
from typing import Optional
import re
# from passlib.context import CryptContext
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

logger = logging.getLogger(__name__)

# Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength
    
    Requirements:
    - At least 8 characters
    - Contains at least one letter
    - Contains at least one number
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="密码长度必须至少8个字符"
        )
    
    if len(password) > 72:
        raise HTTPException(
            status_code=400,
            detail="密码长度不能超过72个字符（bcrypt限制）"
        )
    
    # Check for at least one letter and one number
    if not re.search(r'[a-zA-Z]', password):
        raise HTTPException(
            status_code=400,
            detail="密码必须包含至少一个字母"
        )
    
    if not re.search(r'\d', password):
        raise HTTPException(
            status_code=400,
            detail="密码必须包含至少一个数字"
        )
    
    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Validate password length first
    if not plain_password or len(plain_password) > 72:
        logger.warning("Password verification failed: invalid length")
        return False
    
    # Use bcrypt directly to avoid passlib compatibility issues
    try:
        result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        if not result:
            logger.info("Password verification failed: incorrect password")
        return result
    except ValueError as e:
        logger.error(f"Bcrypt ValueError during password verification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash with validation"""
    # Validate password strength before hashing
    validate_password_strength(password)
    
    # return pwd_context.hash(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        username: str = payload.get("username")
        
        if sub is None:
            raise credentials_exception
        
        # Convert sub to int (it's stored as string in the token)
        try:
            user_id = int(sub)
        except (ValueError, TypeError):
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


def require_role(allowed_roles: list):
    """Dependency to require specific roles"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker


async def get_user_from_token(
    token: str,
    db: AsyncSession
) -> User:
    """Get user from token string (for URL parameter authentication)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        
        if sub is None:
            raise credentials_exception
        
        user_id = int(sub)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise credentials_exception
    return user

