"""
User Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole, ROLE_DISPLAY_NAMES


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.BIDDING  # Default to lowest permission role


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: UserRole
    role_display: Optional[str] = None  # Chinese display name
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    permissions: Optional[List[str]] = None  # List of permission strings

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_permissions(cls, user, permissions: List[str] = None):
        """Create response with permissions"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            role_display=ROLE_DISPLAY_NAMES.get(user.role, str(user.role)),
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            permissions=permissions
        )


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None  # Refresh token for token renewal
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # Seconds until access token expires
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class TokenData(BaseModel):
    """Schema for JWT token data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class RoleOption(BaseModel):
    """Schema for role dropdown options"""
    value: str
    label: str


class RoleListResponse(BaseModel):
    """Schema for available roles list"""
    roles: List[RoleOption]
