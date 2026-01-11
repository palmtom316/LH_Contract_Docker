from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import ExpenseCategory  # Assuming we can reuse or need new enums

class ZeroHourLabor(Base):
    """
    Zero-hour Labor Model (零星用工)
    """
    __tablename__ = "zero_hour_labor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core Fields
    labor_date = Column(Date, nullable=False, index=True)  # 用工时间 (Date)
    attribution = Column(String(50), nullable=False)  # 用工归属: COMPANY/PROJECT (Store as string or Enum)
    
    # Project Specific
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="SET NULL"), nullable=True)
    dispatch_unit = Column(String(200), nullable=True)  # 派工单位
    dispatch_file_path = Column(String(500), nullable=True)  # 派工单文件路径
    dispatch_file_key = Column(String(500), nullable=True)
    dispatch_file_storage = Column(String(50), default='local')
    
    # Labor Details - Skilled (技工)
    skilled_unit_price = Column(Numeric(15, 2), default=0)
    skilled_quantity = Column(Numeric(15, 2), default=0)
    skilled_price_total = Column(Numeric(15, 2), default=0)
    
    # Labor Details - General (普工)
    general_unit_price = Column(Numeric(15, 2), default=0)
    general_quantity = Column(Numeric(15, 2), default=0)
    general_price_total = Column(Numeric(15, 2), default=0)
    
    # Labor Total (for backward compatibility)
    labor_type = Column(String(50), nullable=True)  # DEPRECATED
    labor_unit_price = Column(Numeric(15, 2), default=0)  # DEPRECATED
    labor_quantity = Column(Numeric(15, 2), default=0)  # DEPRECATED
    labor_price_total = Column(Numeric(15, 2), default=0)
    
    # Vehicle Details
    vehicle_quantity = Column(Numeric(15, 2), default=0)
    vehicle_unit_price = Column(Numeric(15, 2), default=0)
    vehicle_price_total = Column(Numeric(15, 2), default=0)
    
    # Material Details (DEPRECATED - Moved to ZeroHourLaborMaterial)
    # material_name = Column(String(200), nullable=True)
    # material_quantity = Column(Numeric(15, 2), default=0)
    # material_unit_price = Column(Numeric(15, 2), default=0)
    # material_price_total = Column(Numeric(15, 2), default=0)
    
    # Summary
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Approval Status
    approval_status = Column(String(50), nullable=True, default="DRAFT")
    feishu_instance_code = Column(String(100), nullable=True)
    approval_pdf_path = Column(String(500), nullable=True)
    approval_pdf_key = Column(String(500), nullable=True)
    approval_pdf_storage = Column(String(50), default='local')
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    upstream_contract = relationship("ContractUpstream")
    creator = relationship("User", foreign_keys=[created_by])
    materials = relationship("ZeroHourLaborMaterial", back_populates="zero_hour_labor", cascade="all, delete-orphan")

    @property
    def material_price_total(self):
        return sum([m.material_price_total for m in self.materials]) if self.materials else 0

    def __repr__(self):
        return f"<ZeroHourLabor(id={self.id}, date={self.labor_date}, total={self.total_amount})>"


class ZeroHourLaborMaterial(Base):
    """
    Zero-hour Labor Materials (零星用工-零星材料)
    """
    __tablename__ = "zero_hour_labor_materials"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zero_hour_labor_id = Column(Integer, ForeignKey("zero_hour_labor.id", ondelete="CASCADE"), nullable=False)
    
    material_name = Column(String(200), nullable=False)
    material_unit = Column(String(50), nullable=True)
    material_quantity = Column(Numeric(15, 2), default=0)
    material_unit_price = Column(Numeric(15, 2), default=0)
    material_price_total = Column(Numeric(15, 2), default=0)
    
    zero_hour_labor = relationship("ZeroHourLabor", back_populates="materials")
