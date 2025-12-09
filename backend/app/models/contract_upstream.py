"""
Upstream Contract Models (上游合同 - 甲方合同)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ContractCategory(str, enum.Enum):
    """合同类别"""
    GENERAL = "总包合同"
    SUB_PRO = "专业分包"
    SUB_LABOR = "劳务分包"
    SERVICE = "技术服务"
    MAINTAIN = "运营维护"
    OTHER = "其他合同"


class CompanyCategory(str, enum.Enum):
    """公司合同分类"""
    CITY_DIST = "市区配网"
    NORTH_DIST = "市北配网"
    USER_ENG = "用户工程"
    MAINT_ENG = "维护工程"
    SUBSTATION = "变电工程"
    MARKETING = "营销工程"
    BEIYUAN = "北源工程"
    ANCHI = "安驰工程"


class PricingMode(str, enum.Enum):
    """计价模式"""
    FIXED_TOTAL = "总价包干"
    FIXED_UNIT = "单价包干"
    LABOR_UNIT = "工日单价"
    RATE_FLOAT = "费率下浮"


class ManagementMode(str, enum.Enum):
    """管理模式"""
    SELF = "自营"
    COOP = "合作"
    AFFILIATE = "挂靠"


class ReceivableCategory(str, enum.Enum):
    """Receivable category enumeration"""
    ADVANCE_PAYMENT = "预付款"           # 预付款
    PROGRESS_PAYMENT = "进度款"          # 进度款
    SETTLEMENT_PAYMENT = "结算款"        # 结算款
    RETENTION_MONEY = "质保金"           # 质保金
    OTHER = "其他"                       # 其他


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
    category = Column(String(50), nullable=True) # Store as string to avoid enum migration issues for now
    company_category = Column(String(50), nullable=True)
    pricing_mode = Column(String(50), nullable=True)
    management_mode = Column(String(50), nullable=True)
    
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
    contract_file_path = Column(String(500), nullable=True)
    
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
    
    category = Column(SQLEnum(ReceivableCategory), nullable=False)  # 款项类别
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 应收金额
    description = Column(String(300), nullable=True)                 # 说明
    expected_date = Column(Date, nullable=True)                      # 预计收款日期
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
    Upstream invoices issued (上游开票记录)
    Represents invoices we issue to Party A
    """
    __tablename__ = "finance_upstream_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    invoice_number = Column(String(50), unique=True, nullable=False)  # 发票号码
    invoice_date = Column(Date, nullable=False)                       # 开票日期
    amount = Column(Numeric(15, 2), nullable=False, default=0)        # 开票金额
    tax_rate = Column(Numeric(5, 2), nullable=True)                   # 税率
    tax_amount = Column(Numeric(15, 2), nullable=True)                # 税额
    
    invoice_type = Column(String(50), nullable=True)                  # 发票类型
    description = Column(String(300), nullable=True)                  # 说明
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
    Upstream receipts (上游收款记录)
    Represents payments received from Party A
    """
    __tablename__ = "finance_upstream_receipts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    receipt_date = Column(Date, nullable=False)                      # 收款日期
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 收款金额
    payment_method = Column(String(50), nullable=True)               # 付款方式
    payer_name = Column(String(200), nullable=True)                  # 付款方名称
    payer_account = Column(String(100), nullable=True)               # 付款方账号
    
    description = Column(String(300), nullable=True)                 # 说明
    file_path = Column(String(500), nullable=True)                   # 凭证文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("ContractUpstream", back_populates="receipts")
    
    def __repr__(self):
        return f"<FinanceUpstreamReceipt(id={self.id}, date={self.receipt_date}, amount={self.amount})>"


class ProjectSettlement(Base):
    """
    Project settlement records (项目结算记录)
    Final settlement for upstream contracts
    """
    __tablename__ = "project_settlements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=False, index=True)
    
    settlement_code = Column(String(50), unique=True, nullable=False)  # 结算编号
    settlement_date = Column(Date, nullable=False)                     # 结算日期
    settlement_amount = Column(Numeric(15, 2), nullable=False, default=0)  # 结算金额
    
    audit_amount = Column(Numeric(15, 2), nullable=True)               # 审核金额
    final_amount = Column(Numeric(15, 2), nullable=True)               # 最终金额
    
    status = Column(String(50), default="待审核")                       # 结算状态
    description = Column(Text, nullable=True)                          # 说明
    file_path = Column(String(500), nullable=True)                     # 结算文件路径
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("ContractUpstream", back_populates="settlements")
    
    def __repr__(self):
        return f"<ProjectSettlement(id={self.id}, code={self.settlement_code}, amount={self.settlement_amount})>"
