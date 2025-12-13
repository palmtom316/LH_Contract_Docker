"""
Management Contract Models (管理合同)
Structure: Same as Downstream (Req 3.4)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ContractCategory, PricingMode, ManagementMode, PaymentCategory

class ContractManagement(Base):
    """
    Management contract model (管理合同)
    Structure: Same as Downstream
    """
    __tablename__ = "contracts_management"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number = Column(Integer, unique=True, nullable=True, index=True)
    contract_code = Column(String(50), unique=True, nullable=False, index=True)
    contract_name = Column(String(200), nullable=False)
    
    # Parties
    party_a_name = Column(String(200), nullable=False)    # 甲方 (Us)
    party_b_name = Column(String(200), nullable=False, index=True)    # 乙方 (Supplier/Landlord/etc)
    
    # Link to upstream contract
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    # Remove snapshot
    # upstream_contract_name_snapshot = Column(String(200), nullable=True)
    
    # Classification
    category = Column(String(50), nullable=True)
    company_category = Column(String(50), nullable=True)
    pricing_mode = Column(SQLEnum(PricingMode), nullable=True)
    management_mode = Column(SQLEnum(ManagementMode), nullable=True)
    
    # Details
    responsible_person = Column(String(100), nullable=True)
    
    party_a_contact = Column(String(100), nullable=True)
    party_a_phone = Column(String(20), nullable=True)
    
    party_b_contact = Column(String(100), nullable=True)
    party_b_phone = Column(String(20), nullable=True)
    
    contract_amount = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Dates
    sign_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # File attachments
    contract_file_path = Column(String(500), nullable=True)
    
    # Status and notes
    status = Column(String(50), default="执行中", index=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    payables = relationship("FinanceManagementPayable", back_populates="contract", cascade="all, delete-orphan")
    invoices = relationship("FinanceManagementInvoice", back_populates="contract", cascade="all, delete-orphan")
    payments = relationship("FinanceManagementPayment", back_populates="contract", cascade="all, delete-orphan")
    settlements = relationship("ManagementSettlement", back_populates="contract", cascade="all, delete-orphan")
    upstream_contract = relationship("ContractUpstream")

    @property
    def total_payable(self):
        return sum((item.amount or 0) for item in self.payables)

    @property
    def total_invoiced(self):
        return sum((item.amount or 0) for item in self.invoices)

    @property
    def total_paid(self):
        return sum((item.amount or 0) for item in self.payments)
        
    @property
    def total_settlement(self):
        return sum((item.settlement_amount or 0) for item in self.settlements)

    @property
    def upstream_contract_name(self):
        return self.upstream_contract.contract_name if self.upstream_contract else None
    
    def __repr__(self):
        return f"<ContractManagement(id={self.id}, code={self.contract_code}, name={self.contract_name})>"



class FinanceManagementPayable(Base):
    """Management payables (管理合同-应付款)"""
    __tablename__ = "finance_management_payables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_management.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    category = Column(SQLEnum(PaymentCategory), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False, default=0)
    description = Column(String(300), nullable=True)
    expected_date = Column(Date, nullable=True)
    file_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    contract = relationship("ContractManagement", back_populates="payables")


class FinanceManagementInvoice(Base):
    """Management invoices (管理合同-收票/挂账)"""
    __tablename__ = "finance_management_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_management.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False, default=0)
    
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    
    invoice_type = Column(String(50), nullable=True)
    supplier_name = Column(String(200), nullable=True)
    description = Column(String(300), nullable=True)
    file_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    contract = relationship("ContractManagement", back_populates="invoices")


class FinanceManagementPayment(Base):
    """Management payments (管理合同-付款)"""
    __tablename__ = "finance_management_payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_management.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False, default=0)
    
    payment_method = Column(String(50), nullable=True)
    payee_name = Column(String(200), nullable=True)
    payee_account = Column(String(100), nullable=True)
    payee_bank = Column(String(200), nullable=True)
    
    description = Column(String(300), nullable=True)
    file_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    contract = relationship("ContractManagement", back_populates="payments")


class ManagementSettlement(Base):
    """Management settlement (管理合同-结算)"""
    __tablename__ = "management_settlements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_management.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    settlement_code = Column(String(50), nullable=True)
    settlement_date = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)
    warranty_date = Column(Date, nullable=True)
    settlement_amount = Column(Numeric(15, 2), nullable=False, default=0)
    
    audit_amount = Column(Numeric(15, 2), nullable=True)
    final_amount = Column(Numeric(15, 2), nullable=True)
    
    status = Column(String(50), default="待审核")
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    contract = relationship("ContractManagement", back_populates="settlements")
