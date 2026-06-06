"""
Non-Contract Expense Models (非合同费用 - 无合同费用报销)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ExpenseCategory, ExpenseType

class ExpenseNonContract(Base):
    """
    Non-contract expense model (无合同费用报销)
    Req 3.4: 特有子表-无合同费用报销
    """
    __tablename__ = "expenses_non_contract"
    CATEGORY_FIELD = "category"
    EXPENSE_TYPE_FIELD = "expense_type"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_code = Column(String(50), unique=True, nullable=False, index=True)  # 序号/编号
    
    # Classification
    attribution = Column(String(50), nullable=True)  # 费用归属 (Company/Project)
    category = Column(String(50), nullable=False)  # 费用类别（公司费用/项目费用）
    expense_type = Column(String(50), nullable=True)  # 费用分类/费用类别字典值（如管理费、培训费）
    
    # Details
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 金额 (Implied essential field)
    expense_date = Column(Date, nullable=False)                      # 发生日期
    
    handler = Column(String(100), nullable=True)                     # 经办人
    responsible_person = Column(String(100), nullable=True)          # 负责人
    
    # Link to Upstream Contract
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    
    description = Column(Text, nullable=True)                        # 说明
    
    # File attachments
    file_path = Column(String(500), nullable=True)                   # 凭证文件路径 (PDF Only)
    file_key = Column(String(500), nullable=True)
    storage_provider = Column(String(50), default='local')
    
    # Status (Optional/Standard)
    status = Column(String(50), default="待审核", index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Feishu Approval Integration (V1.4)
    approval_status = Column(String(50), nullable=True, default="DRAFT")  # DRAFT, PENDING, APPROVED, REJECTED
    feishu_instance_code = Column(String(100), nullable=True)  # 飞书审批实例ID
    approval_pdf_path = Column(String(500), nullable=True)  # 审批PDF本地路径
    approval_pdf_key = Column(String(500), nullable=True)
    approval_pdf_storage = Column(String(50), default='local')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    upstream_contract = relationship("ContractUpstream", foreign_keys=[upstream_contract_id])
    
    def __repr__(self):
        return f"<ExpenseNonContract(id={self.id}, code={self.expense_code}, amount={self.amount})>"
