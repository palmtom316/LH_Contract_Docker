"""
User and Role Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "ADMIN"          # 管理员 - 完全权限
    MANAGER = "MANAGER"      # 经理 - 查看所有、编辑权限
    OPERATOR = "OPERATOR"    # 操作员 - 录入和编辑
    VIEWER = "VIEWER"        # 查看者 - 只读权限


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # Role-based access control
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
