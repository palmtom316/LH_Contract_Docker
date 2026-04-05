from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class SysDictionary(Base):
    """
    System Data Dictionary for dynamic dropdown options.
    """
    __tablename__ = "sys_dictionaries"
    PROTECTED_CATEGORIES = {"expense_type", "payment_category", "contract_category", "project_category"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, index=True) # e.g., 'contract_category', 'pricing_mode'
    label = Column(String(200), nullable=False) # Display text: 'General Contract'
    value = Column(String(200), nullable=False) # Stored value: 'GENERAL' or 'General Contract' (Usually same as label for flexibility)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def is_protected_category(self) -> bool:
        return self.category in self.PROTECTED_CATEGORIES

class SystemConfig(Base):
    """
    System Configuration (Key-Value storage for branding etc)
    """
    __tablename__ = "sys_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True) # e.g., 'system_name', 'system_logo'
    value = Column(String(500), nullable=True)
    description = Column(String(200), nullable=True)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
