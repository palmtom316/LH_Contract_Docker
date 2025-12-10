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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_code = Column(String(50), unique=True, nullable=False, index=True)  # 序号/编号
    
    # Classification
    category = Column(String(50), nullable=False)  # 费用类别 (Company/Project)
    expense_type = Column(String(50), nullable=True)  # 费用分类 (Management, Training, etc.)
    
    # Details
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 金额 (Implied essential field)
    expense_date = Column(Date, nullable=False)                      # 发生日期
    
    handler = Column(String(100), nullable=True)                     # 经办人
    responsible_person = Column(String(100), nullable=True)          # 负责人
    
    # Link to Upstream Contract
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="SET NULL"), nullable=True, index=True)
    
    description = Column(Text, nullable=True)                        # 说明
    
    # File attachments
    file_path = Column(String(500), nullable=True)                   # 凭证文件路径 (PDF Only)
    
    # Status (Optional/Standard)
    status = Column(String(50), default="待审核")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    upstream_contract = relationship("ContractUpstream", foreign_keys=[upstream_contract_id])
    
    def __repr__(self):
        return f"<ExpenseNonContract(id={self.id}, code={self.expense_code}, amount={self.amount})>"
