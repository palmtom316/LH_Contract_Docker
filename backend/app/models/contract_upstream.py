"""
Upstream Contract Models (上游合同 - 甲方合同)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ContractCategory, PricingMode, ManagementMode, PaymentCategory

class ContractUpstream(Base):
    """Upstream Contract Model"""
    __tablename__ = "contracts_upstream"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_code = Column(String(50), unique=True, nullable=False, index=True)
    contract_name = Column(String(200), nullable=False)
    
    # Parties
    party_a_name = Column(String(200), nullable=False, index=True)
    party_b_name = Column(String(200), nullable=False)  # 乙方
    
    # Classification
    category = Column(SQLEnum(ContractCategory), nullable=True)
    company_category = Column(String(50), nullable=True) # Keep as string or define enum if needed
    pricing_mode = Column(SQLEnum(PricingMode), nullable=True)
    management_mode = Column(SQLEnum(ManagementMode), nullable=True)
    
    # Details
    responsible_person = Column(String(100), nullable=True) # 负责人
    
    party_a_contact = Column(String(100), nullable=True)
    party_a_phone = Column(String(20), nullable=True)
    
    project_name = Column(String(200), nullable=True)
    project_location = Column(String(300), nullable=True)
    
    contract_amount = Column(Numeric(15, 2), default=0)
    
    # Dates
    sign_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    status = Column(String(50), default="进行中")
    notes = Column(Text, nullable=True)
    contract_file_path = Column(String(500), nullable=True) # Contract File (PDF Only)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    receivables = relationship("FinanceUpstreamReceivable", back_populates="contract", cascade="all, delete-orphan")
    invoices = relationship("FinanceUpstreamInvoice", back_populates="contract", cascade="all, delete-orphan")
    receipts = relationship("FinanceUpstreamReceipt", back_populates="contract", cascade="all, delete-orphan")
    settlements = relationship("ProjectSettlement", back_populates="contract", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ContractUpstream(id={self.id}, code={self.contract_code}, name={self.contract_name})>"


class FinanceUpstreamReceivable(Base):
    """
    Upstream receivables (上游应收款)
    Represents planned receivable amounts for upstream contracts
    """
    __tablename__ = "finance_upstream_receivables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    category = Column(SQLEnum(PaymentCategory), nullable=False)  # 应收款类别
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 应收金额
    description = Column(String(300), nullable=True)                 # 说明
    expected_date = Column(Date, nullable=True)                      # 形成/预计日期
    file_path = Column(String(500), nullable=True)                   # 审批文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("ContractUpstream", back_populates="receivables")
    
    def __repr__(self):
        return f"<FinanceUpstreamReceivable(id={self.id}, category={self.category}, amount={self.amount})>"


class FinanceUpstreamInvoice(Base):
    """
    Upstream invoices issued (上游开票 - 挂账)
    Represents invoices we issue to Party A
    """
    __tablename__ = "finance_upstream_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    invoice_number = Column(String(50), nullable=True)  # 发票号码 (Made nullable as per some flows, but usually strictly required)
    invoice_date = Column(Date, nullable=False)                       # 挂账日期/开票日期
    amount = Column(Numeric(15, 2), nullable=False, default=0)        # 金额
    
    # Optional extended fields
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    
    description = Column(String(300), nullable=True)
    file_path = Column(String(500), nullable=True)                    # 发票文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("ContractUpstream", back_populates="invoices")
    
    def __repr__(self):
        return f"<FinanceUpstreamInvoice(id={self.id}, number={self.invoice_number}, amount={self.amount})>"


class FinanceUpstreamReceipt(Base):
    """
    Upstream receipts (上游收款)
    """
    __tablename__ = "finance_upstream_receipts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    receipt_date = Column(Date, nullable=False)                      # 收款时间
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 金额
    
    payment_method = Column(String(50), nullable=True)
    payer_name = Column(String(200), nullable=True)
    
    description = Column(String(300), nullable=True)
    file_path = Column(String(500), nullable=True)                   # 银行回单文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("ContractUpstream", back_populates="receipts")
    
    def __repr__(self):
        return f"<FinanceUpstreamReceipt(id={self.id}, date={self.receipt_date}, amount={self.amount})>"


class ProjectSettlement(Base):
    """
    Project settlement records (项目结算)
    """
    __tablename__ = "project_settlements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Dates
    start_date = Column(Date, nullable=True)            # 开工时间
    end_date = Column(Date, nullable=True)              # 竣工时间
    submission_date = Column(Date, nullable=True)       # 报审日期
    completion_date = Column(Date, nullable=True)       # 办结日期
    
    settlement_amount = Column(Numeric(15, 2), nullable=False, default=0)  # 结算金额
    settlement_batch = Column(String(50), nullable=True) # 结算批次
    
    # Files
    audit_report_path = Column(String(500), nullable=True) # 审核报告路径
    start_report_path = Column(String(500), nullable=True) # 开工报告路径
    finish_report_path = Column(String(500), nullable=True) # 竣工报告路径
    
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("ContractUpstream", back_populates="settlements")
    
    def __repr__(self):
        return f"<ProjectSettlement(id={self.id}, amount={self.settlement_amount})>"
