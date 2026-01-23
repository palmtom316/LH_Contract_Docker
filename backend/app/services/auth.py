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
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token_sync(data: dict, jti: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token with JTI for tracking (sync version for token generation only)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire


async def create_refresh_token_with_db(
    data: dict, 
    db: AsyncSession,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token and store in database for rotation/revocation support.
    
    Returns:
        The encoded JWT refresh token string
    """
    import uuid
    from app.models.refresh_token import RefreshToken
    
    # Generate unique JTI
    jti = str(uuid.uuid4())
    
    # Create the token
    token, expires_at = create_refresh_token_sync(data, jti, expires_delta)
    
    # Store in database
    user_id = int(data.get("sub"))
    refresh_token_record = RefreshToken(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
        revoked=False
    )
    db.add(refresh_token_record)
    await db.commit()
    
    logger.info(f"[AUTH] Created refresh token with JTI {jti[:8]}... for user {user_id}")
    return token


async def verify_refresh_token_with_db(token: str, db: AsyncSession) -> Optional[dict]:
    """
    Verify refresh token and check if it's revoked in the database.
    Returns payload if valid, None otherwise.
    """
    from app.models.refresh_token import RefreshToken
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Ensure this is a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            return None
        
        # Check JTI in database
        jti = payload.get("jti")
        if not jti:
            logger.warning("Refresh token missing JTI - legacy token")
            # For backwards compatibility, allow tokens without JTI but log warning
            return payload
        
        # Verify token is not revoked
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            logger.warning(f"Refresh token JTI {jti[:8]}... not found in database")
            return None
        
        if token_record.revoked:
            logger.warning(f"Refresh token JTI {jti[:8]}... has been revoked")
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.info("Refresh token has expired")
        return None
    except jwt.PyJWTError as e:
        logger.error(f"Refresh token verification failed: {e}")
        return None


async def revoke_refresh_token(jti: str, db: AsyncSession) -> bool:
    """Revoke a specific refresh token by its JTI"""
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import update
    
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.jti == jti)
        .values(revoked=True)
    )
    await db.commit()
    
    if result.rowcount > 0:
        logger.info(f"[AUTH] Revoked refresh token JTI {jti[:8]}...")
        return True
    return False


async def revoke_all_user_tokens(user_id: int, db: AsyncSession) -> int:
    """Revoke all refresh tokens for a user (e.g., on logout or password change)"""
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import update
    
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        .values(revoked=True)
    )
    await db.commit()
    
    logger.info(f"[AUTH] Revoked {result.rowcount} refresh tokens for user {user_id}")
    return result.rowcount


# Keep legacy function for backwards compatibility
def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Verify refresh token and return payload if valid (legacy sync version).
    Returns None if token is invalid or not a refresh token.
    NOTE: This does NOT check database revocation. Use verify_refresh_token_with_db for full security.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Ensure this is a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.info("Refresh token has expired")
        return None
    except jwt.PyJWTError as e:
        logger.error(f"Refresh token verification failed: {e}")
        return None


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

