"""
Downstream Contract Models (下游合同 - 乙方/供应商合同)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ContractCategory, DownstreamContractCategory, PricingMode, ManagementMode, PaymentCategory

class ContractDownstream(Base):
    """
    Downstream contract model (下游合同/供应商合同)
    Contracts with subcontractors, suppliers, etc.
    """
    __tablename__ = "contracts_downstream"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number = Column(Integer, unique=True, nullable=True, index=True)
    contract_code = Column(String(50), unique=True, nullable=False, index=True)  # 合同编号
    contract_name = Column(String(200), nullable=False)                           # 合同名称
    
    # Parties
    party_a_name = Column(String(200), nullable=False)    # 甲方 (Usually Us)
    party_b_name = Column(String(200), nullable=False, index=True)    # 乙方 (Supplier/Subcontractor)
    
    # Link to upstream contract
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    # Remove snapshot as per normalization
    # upstream_contract_name_snapshot = Column(String(200), nullable=True)
    
    # Classification (Matching Upstream structure as per Req 3.3)
    category = Column(String(50), nullable=True)  # 合同类别 - 使用字符串避免枚举冲突
    company_category = Column(String(50), nullable=True)
    pricing_mode = Column(SQLEnum(PricingMode), nullable=True)
    management_mode = Column(SQLEnum(ManagementMode), nullable=True)
    
    # Details
    responsible_person = Column(String(100), nullable=True) # 负责人
    
    party_a_contact = Column(String(100), nullable=True)
    party_a_phone = Column(String(20), nullable=True)
    
    party_b_contact = Column(String(100), nullable=True) # Supplier Contact
    party_b_phone = Column(String(20), nullable=True)
    
    contract_amount = Column(Numeric(15, 2), nullable=False, default=0)  # 合同金额
    
    # Dates
    sign_date = Column(Date, nullable=True)                   # 签订日期
    start_date = Column(Date, nullable=True)                  # 开始日期
    end_date = Column(Date, nullable=True)                    # 结束日期
    
    # File attachments
    contract_file_path = Column(String(500), nullable=True)   # 合同文件路径 (PDF Only)
    
    # Status and notes
    # Status and notes
    status = Column(String(50), default="执行中", index=True)              # 合同状态
    notes = Column(Text, nullable=True)                       # 备注
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    upstream_contract = relationship("ContractUpstream")

    @property
    def upstream_contract_name(self):
        return self.upstream_contract.contract_name if self.upstream_contract else None

    payables = relationship("FinanceDownstreamPayable", back_populates="contract", cascade="all, delete-orphan")
    invoices = relationship("FinanceDownstreamInvoice", back_populates="contract", cascade="all, delete-orphan")
    payments = relationship("FinanceDownstreamPayment", back_populates="contract", cascade="all, delete-orphan")
    settlements = relationship("DownstreamSettlement", back_populates="contract", cascade="all, delete-orphan")
    
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

    def __repr__(self):
        return f"<ContractDownstream(id={self.id}, code={self.contract_code}, party_b={self.party_b_name})>"


class FinanceDownstreamPayable(Base):
    """
    Downstream payables (下游应付款)
    Represents planned payable amounts for downstream contracts
    """
    __tablename__ = "finance_downstream_payables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    category = Column(SQLEnum(PaymentCategory), nullable=False)  # 款项类别
    amount = Column(Numeric(15, 2), nullable=False, default=0)   # 应付金额
    description = Column(String(300), nullable=True)             # 说明
    expected_date = Column(Date, nullable=True)                  # 预计付款日期
    file_path = Column(String(500), nullable=True)               # 审批文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    contract = relationship("ContractDownstream", back_populates="payables")
    
    def __repr__(self):
        return f"<FinanceDownstreamPayable(id={self.id}, category={self.category}, amount={self.amount})>"


class FinanceDownstreamInvoice(Base):
    """
    Downstream invoices received (下游收票 - 挂账)
    Represents invoices received from suppliers/subcontractors
    """
    __tablename__ = "finance_downstream_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    invoice_number = Column(String(50), nullable=False)              # 发票号码
    invoice_date = Column(Date, nullable=False)                      # 发票日期
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 发票金额
    
    tax_rate = Column(Numeric(5, 2), nullable=True)                  # 税率
    tax_amount = Column(Numeric(15, 2), nullable=True)               # 税额
    
    invoice_type = Column(String(50), nullable=True)                 # 发票类型
    supplier_name = Column(String(200), nullable=True)               # 开票方名称
    description = Column(String(300), nullable=True)                 # 说明
    file_path = Column(String(500), nullable=True)                   # 发票文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    contract = relationship("ContractDownstream", back_populates="invoices")
    
    def __repr__(self):
        return f"<FinanceDownstreamInvoice(id={self.id}, number={self.invoice_number}, amount={self.amount})>"


class FinanceDownstreamPayment(Base):
    """
    Downstream payments (下游付款记录 - 实付)
    Represents payments made to suppliers/subcontractors
    """
    __tablename__ = "finance_downstream_payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    payment_date = Column(Date, nullable=False)                      # 付款日期
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 付款金额
    
    payment_method = Column(String(50), nullable=True)               # 付款方式
    payee_name = Column(String(200), nullable=True)                  # 收款方名称
    payee_account = Column(String(100), nullable=True)               # 收款方账号
    payee_bank = Column(String(200), nullable=True)                  # 收款方银行
    
    description = Column(String(300), nullable=True)                 # 说明
    file_path = Column(String(500), nullable=True)                   # 凭证文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    contract = relationship("ContractDownstream", back_populates="payments")
    
    def __repr__(self):
        return f"<FinanceDownstreamPayment(id={self.id}, date={self.payment_date}, amount={self.amount})>"


class DownstreamSettlement(Base):
    """
    Downstream settlement records (下游结算记录)
    Final settlement for downstream contracts
    """
    __tablename__ = "downstream_settlements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    
    settlement_code = Column(String(50), nullable=True)  # 结算编号
    settlement_date = Column(Date, nullable=False)                     # 结算办结日期
    completion_date = Column(Date, nullable=True)                      # 完工日期
    warranty_date = Column(Date, nullable=True)                        # 质保到期日期
    settlement_amount = Column(Numeric(15, 2), nullable=False, default=0)  # 结算金额
    
    audit_amount = Column(Numeric(15, 2), nullable=True)               # 审核金额
    final_amount = Column(Numeric(15, 2), nullable=True)               # 最终金额
    
    status = Column(String(50), default="待审核")                       # 结算状态
    description = Column(Text, nullable=True)                          # 说明
    file_path = Column(String(500), nullable=True)                     # 结算文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    contract = relationship("ContractDownstream", back_populates="settlements")
    
    def __repr__(self):
        return f"<DownstreamSettlement(id={self.id}, code={self.settlement_code}, amount={self.settlement_amount})>"
