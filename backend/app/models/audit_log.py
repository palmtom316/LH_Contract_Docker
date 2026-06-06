"""
Audit Log Model - 审计日志模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    """Audit log model for tracking user operations"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User info
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(50), nullable=True)  # Store username in case user is deleted
    
    # Action info
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = Column(String(50), nullable=False)  # Contract, User, Payment, etc.
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    resource_name = Column(String(255), nullable=True)  # Name/identifier for display
    
    # Details
    description = Column(Text, nullable=True)  # Human-readable description
    old_values = Column(Text, nullable=True)  # JSON string of old values (for updates)
    new_values = Column(Text, nullable=True)  # JSON string of new values (for updates)
    
    # Request info
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship
    user = relationship("User", backref="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, action={self.action}, resource={self.resource_type})>"
