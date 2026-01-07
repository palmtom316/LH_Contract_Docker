"""
User and Role Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration - 按照业务部门分类"""
    ADMIN = "ADMIN"                     # 管理员 - 系统全部权限
    COMPANY_LEADER = "COMPANY_LEADER"   # 公司领导 - 查看主页概况、经营看板、报表统计，可下载报表
    CONTRACT_MANAGER = "CONTRACT_MANAGER"  # 合同管理 - 合同CRUD、财务记录CRUD、无合同费用CRUD、查看报表
    FINANCE = "FINANCE"                 # 财务部 - 查看报表、财务记录CRUD、无合同费用CRUD
    ENGINEERING = "ENGINEERING"         # 工程部 - 查看合同基本信息、应收应付结算CRUD、无合同费用CRUD
    AUDIT = "AUDIT"                     # 审计部 - 查看合同基本信息、结算记录CRUD、无合同费用CRUD（仅限本人数据）
    BIDDING = "BIDDING"                 # 投标部 - 查看上游合同基本信息、无合同费用CRUD（仅限本人数据）
    GENERAL_AFFAIRS = "GENERAL_AFFAIRS" # 综合部 - 无合同费用CRUD、管理合同财务记录CRUD


# Role display names for frontend
ROLE_DISPLAY_NAMES = {
    UserRole.ADMIN: "管理员",
    UserRole.COMPANY_LEADER: "公司领导",
    UserRole.CONTRACT_MANAGER: "合同管理",
    UserRole.FINANCE: "财务部",
    UserRole.ENGINEERING: "工程部",
    UserRole.AUDIT: "审计部",
    UserRole.BIDDING: "投标部",
    UserRole.GENERAL_AFFAIRS: "综合部",
}


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # Role-based access control
    role = Column(SQLEnum(UserRole), default=UserRole.BIDDING, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    @property
    def role_display_name(self) -> str:
        """Get Chinese display name for role"""
        return ROLE_DISPLAY_NAMES.get(self.role, str(self.role))
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
