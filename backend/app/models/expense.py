"""
Non-Contract Expense Models (非合同费用)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.database import Base


class ExpenseCategoryType(str, enum.Enum):
    """Expense category type enumeration"""
    DAILY_OPERATIONS = "日常运营"         # 日常运营费用
    EQUIPMENT = "设备"                    # 设备相关费用
    VEHICLE = "车辆"                      # 车辆相关费用
    PERSONNEL = "人员"                    # 人员相关费用
    OFFICE = "办公"                       # 办公费用
    TAX = "税费"                          # 税费
    OTHER = "其他"                        # 其他费用


class ExpenseType(str, enum.Enum):
    """Specific expense type enumeration"""
    # Daily Operations
    UTILITIES = "水电费"
    COMMUNICATION = "通讯费"
    RENT = "房租"
    PROPERTY_FEE = "物业费"
    
    # Equipment
    EQUIPMENT_PURCHASE = "设备采购"
    EQUIPMENT_MAINTENANCE = "设备维修"
    EQUIPMENT_RENTAL = "设备租赁"
    
    # Vehicle
    VEHICLE_FUEL = "车辆油费"
    VEHICLE_MAINTENANCE = "车辆维修"
    VEHICLE_INSURANCE = "车辆保险"
    VEHICLE_SERVICE = "车辆年检"
    
    # Personnel
    SALARY = "工资"
    BONUS = "奖金"
    SOCIAL_INSURANCE = "社保"
    TRAINING = "培训费"
    WELFARE = "福利费"
    
    # Office
    OFFICE_SUPPLIES = "办公用品"
    PRINTING = "打印复印"
    TRAVEL = "差旅费"
    ENTERTAINMENT = "招待费"
    
    # Tax
    VAT = "增值税"
    INCOME_TAX = "所得税"
    STAMP_DUTY = "印花税"
    
    # Other
    OTHER = "其他"


class ExpenseNonContract(Base):
    """
    Non-contract expense model (非合同费用)
    For tracking expenses not tied to specific contracts
    """
    __tablename__ = "expenses_non_contract"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_code = Column(String(50), unique=True, nullable=False, index=True)  # 费用编号
    
    # Expense classification
    category = Column(SQLEnum(ExpenseCategoryType), nullable=False)  # 费用大类
    expense_type = Column(SQLEnum(ExpenseType), nullable=False)      # 费用类型
    
    # Amount details
    amount = Column(Numeric(15, 2), nullable=False, default=0)       # 金额
    tax_amount = Column(Numeric(15, 2), nullable=True)               # 税额
    
    # Date information
    expense_date = Column(Date, nullable=False)                      # 费用日期
    payment_date = Column(Date, nullable=True)                       # 付款日期
    
    # Payment details
    payment_method = Column(String(50), nullable=True)               # 付款方式
    payee_name = Column(String(200), nullable=True)                  # 收款方
    invoice_number = Column(String(100), nullable=True)              # 发票号码
    
    # Description
    description = Column(Text, nullable=True)                        # 费用说明
    
    # File attachments
    invoice_file_path = Column(String(500), nullable=True)           # 发票文件路径
    receipt_file_path = Column(String(500), nullable=True)           # 付款凭证路径
    
    # Status
    status = Column(String(50), default="待审核")                     # 状态
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<ExpenseNonContract(id={self.id}, code={self.expense_code}, type={self.expense_type}, amount={self.amount})>"
