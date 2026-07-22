from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
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
    attribution = Column(
        String(50), nullable=False
    )  # 用工归属: COMPANY/PROJECT (Store as string or Enum)

    # Project Specific
    upstream_contract_id = Column(
        Integer, ForeignKey("contracts_upstream.id", ondelete="SET NULL"), nullable=True
    )
    dispatch_unit = Column(String(200), nullable=True)  # 派工单位
    dispatch_file_path = Column(String(500), nullable=True)  # 派工单文件路径
    dispatch_file_key = Column(String(500), nullable=True)
    dispatch_file_storage = Column(String(50), default="local")

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

    # Description and Tax
    description = Column(Text, nullable=True)  # 零星用工说明
    tax_rate = Column(Numeric(5, 2), default=0)  # 税率 (%)
    tax_amount = Column(Numeric(15, 2), default=0)  # 税金

    # Summary
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)  # 含税总金额

    # Approval Status
    approval_status = Column(String(50), nullable=True, default="DRAFT")
    feishu_instance_code = Column(String(100), nullable=True)
    approval_pdf_path = Column(String(500), nullable=True)
    approval_pdf_key = Column(String(500), nullable=True)
    approval_pdf_storage = Column(String(50), default="local")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    upstream_contract = relationship("ContractUpstream")
    creator = relationship("User", foreign_keys=[created_by])
    materials = relationship(
        "ZeroHourLaborMaterial",
        back_populates="zero_hour_labor",
        cascade="all, delete-orphan",
    )
    payables = relationship(
        "ZeroHourLaborPayable",
        back_populates="zero_hour_labor",
        cascade="all, delete-orphan",
    )
    invoices = relationship(
        "ZeroHourLaborInvoice",
        back_populates="zero_hour_labor",
        cascade="all, delete-orphan",
    )
    payments = relationship(
        "ZeroHourLaborPayment",
        back_populates="zero_hour_labor",
        cascade="all, delete-orphan",
    )

    @property
    def material_price_total(self):
        return (
            sum([m.material_price_total for m in self.materials])
            if self.materials
            else 0
        )

    def __repr__(self):
        return f"<ZeroHourLabor(id={self.id}, date={self.labor_date}, total={self.total_amount})>"


class ZeroHourLaborMaterial(Base):
    """
    Zero-hour Labor Materials (零星用工-零星材料)
    """

    __tablename__ = "zero_hour_labor_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zero_hour_labor_id = Column(
        Integer, ForeignKey("zero_hour_labor.id", ondelete="CASCADE"), nullable=False
    )

    material_name = Column(String(200), nullable=False)
    material_unit = Column(String(50), nullable=True)
    material_quantity = Column(Numeric(15, 2), default=0)
    material_unit_price = Column(Numeric(15, 2), default=0)
    material_price_total = Column(Numeric(15, 2), default=0)

    zero_hour_labor = relationship("ZeroHourLabor", back_populates="materials")


class ZeroHourLaborPayable(Base):
    __tablename__ = "finance_zero_hour_payables"
    id = Column(Integer, primary_key=True)
    zero_hour_labor_id = Column(
        Integer,
        ForeignKey("zero_hour_labor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expected_date = Column(Date)
    description = Column(String(300))
    file_path = Column(String(500))
    file_key = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    zero_hour_labor = relationship("ZeroHourLabor", back_populates="payables")


class ZeroHourLaborInvoice(Base):
    __tablename__ = "finance_zero_hour_invoices"
    id = Column(Integer, primary_key=True)
    zero_hour_labor_id = Column(
        Integer,
        ForeignKey("zero_hour_labor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_date = Column(Date, nullable=False)
    invoice_number = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0)
    supplier = Column(String(200))
    file_path = Column(String(500))
    file_key = Column(String(500))
    status = Column(String(30), default="active")
    source_import_item_id = Column(
        Integer, ForeignKey("invoice_import_items.id"), nullable=True, index=True
    )
    source_import_allocation_id = Column(
        Integer, ForeignKey("invoice_import_allocations.id"), nullable=True, unique=True
    )
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    zero_hour_labor = relationship("ZeroHourLabor", back_populates="invoices")


class ZeroHourLaborPayment(Base):
    __tablename__ = "finance_zero_hour_payments"
    id = Column(Integer, primary_key=True)
    zero_hour_labor_id = Column(
        Integer,
        ForeignKey("zero_hour_labor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payee_name = Column(String(200))
    payee_account = Column(String(100))
    payee_bank = Column(String(200))
    payment_method = Column(String(50))
    file_path = Column(String(500))
    file_key = Column(String(500))
    status = Column(String(30), default="active")
    source_bank_receipt_item_id = Column(
        Integer, ForeignKey("bank_receipt_items.id"), nullable=True, index=True
    )
    source_bank_receipt_allocation_id = Column(
        Integer, ForeignKey("bank_receipt_allocations.id"), nullable=True, unique=True
    )
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    zero_hour_labor = relationship("ZeroHourLabor", back_populates="payments")
