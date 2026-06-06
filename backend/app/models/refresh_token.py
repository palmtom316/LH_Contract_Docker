"""
RefreshToken Model
Stores refresh token JTIs for rotation and revocation support
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RefreshToken(Base):
    """
    Stores refresh tokens with JTI (JWT ID) for:
    - Token rotation: invalidate old token when a new one is issued
    - Token revocation: invalidate all user tokens on logout
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, index=True, nullable=False)  # JWT ID (UUID)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    user = relationship("User", backref="refresh_tokens")
