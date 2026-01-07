"""
Permission Definitions and Checkers for RBAC
基于角色的权限控制定义
"""
from enum import Enum
from typing import List, Set
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.services.auth import get_current_active_user


class Permission(str, Enum):
    """System permissions"""
    # Dashboard & Reports
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_REPORTS = "view_reports"
    DOWNLOAD_REPORTS = "download_reports"
    
    # Upstream Contracts
    VIEW_UPSTREAM_CONTRACTS = "view_upstream_contracts"
    VIEW_UPSTREAM_BASIC_INFO = "view_upstream_basic_info"
    CREATE_UPSTREAM_CONTRACTS = "create_upstream_contracts"
    EDIT_UPSTREAM_CONTRACTS = "edit_upstream_contracts"
    DELETE_UPSTREAM_CONTRACTS = "delete_upstream_contracts"
    
    # Downstream Contracts
    VIEW_DOWNSTREAM_CONTRACTS = "view_downstream_contracts"
    VIEW_DOWNSTREAM_BASIC_INFO = "view_downstream_basic_info"
    CREATE_DOWNSTREAM_CONTRACTS = "create_downstream_contracts"
    EDIT_DOWNSTREAM_CONTRACTS = "edit_downstream_contracts"
    DELETE_DOWNSTREAM_CONTRACTS = "delete_downstream_contracts"
    
    # Management Contracts
    VIEW_MANAGEMENT_CONTRACTS = "view_management_contracts"
    VIEW_MANAGEMENT_BASIC_INFO = "view_management_basic_info"
    CREATE_MANAGEMENT_CONTRACTS = "create_management_contracts"
    EDIT_MANAGEMENT_CONTRACTS = "edit_management_contracts"
    DELETE_MANAGEMENT_CONTRACTS = "delete_management_contracts"
    
    # Financial Records - Receivables (应收款)
    VIEW_RECEIVABLES = "view_receivables"
    CREATE_RECEIVABLES = "create_receivables"
    EDIT_RECEIVABLES = "edit_receivables"
    DELETE_RECEIVABLES = "delete_receivables"
    
    # Financial Records - Payables (应付款)
    VIEW_PAYABLES = "view_payables"
    CREATE_PAYABLES = "create_payables"
    EDIT_PAYABLES = "edit_payables"
    DELETE_PAYABLES = "delete_payables"
    
    # Financial Records - Invoices (挂账)
    VIEW_INVOICES = "view_invoices"
    CREATE_INVOICES = "create_invoices"
    EDIT_INVOICES = "edit_invoices"
    DELETE_INVOICES = "delete_invoices"
    
    # Financial Records - Payments (付款/收款)
    VIEW_PAYMENTS = "view_payments"
    CREATE_PAYMENTS = "create_payments"
    EDIT_PAYMENTS = "edit_payments"
    DELETE_PAYMENTS = "delete_payments"
    
    # Financial Records - Settlements (结算)
    VIEW_SETTLEMENTS = "view_settlements"
    CREATE_SETTLEMENTS = "create_settlements"
    EDIT_SETTLEMENTS = "edit_settlements"
    DELETE_SETTLEMENTS = "delete_settlements"
    
    # Non-contract Expenses (无合同费用)
    VIEW_EXPENSES = "view_expenses"
    CREATE_EXPENSES = "create_expenses"
    EDIT_EXPENSES = "edit_expenses"
    DELETE_EXPENSES = "delete_expenses"
    
    # User Management
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    
    # Management Contract Financial Records (管理合同专用)
    MANAGE_MGMT_CONTRACT_FINANCE = "manage_mgmt_contract_finance"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    # 管理员 - 系统全部权限
    UserRole.ADMIN: set(Permission),
    
    # 公司领导 - 查看主页概况、经营看板、报表统计，可下载报表
    UserRole.COMPANY_LEADER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
        Permission.DOWNLOAD_REPORTS,
        Permission.VIEW_UPSTREAM_BASIC_INFO,
        Permission.VIEW_DOWNSTREAM_BASIC_INFO,
        Permission.VIEW_MANAGEMENT_BASIC_INFO,
    },
    
    # 合同管理 - 合同CRUD、财务记录CRUD、无合同费用CRUD、查看报表
    UserRole.CONTRACT_MANAGER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
        Permission.DOWNLOAD_REPORTS,
        # Upstream
        Permission.VIEW_UPSTREAM_CONTRACTS,
        Permission.VIEW_UPSTREAM_BASIC_INFO,
        Permission.CREATE_UPSTREAM_CONTRACTS,
        Permission.EDIT_UPSTREAM_CONTRACTS,
        Permission.DELETE_UPSTREAM_CONTRACTS,
        # Downstream
        Permission.VIEW_DOWNSTREAM_CONTRACTS,
        Permission.VIEW_DOWNSTREAM_BASIC_INFO,
        Permission.CREATE_DOWNSTREAM_CONTRACTS,
        Permission.EDIT_DOWNSTREAM_CONTRACTS,
        Permission.DELETE_DOWNSTREAM_CONTRACTS,
        # Management
        Permission.VIEW_MANAGEMENT_CONTRACTS,
        Permission.VIEW_MANAGEMENT_BASIC_INFO,
        Permission.CREATE_MANAGEMENT_CONTRACTS,
        Permission.EDIT_MANAGEMENT_CONTRACTS,
        Permission.DELETE_MANAGEMENT_CONTRACTS,
        # All Financial Records
        Permission.VIEW_RECEIVABLES, Permission.CREATE_RECEIVABLES, Permission.EDIT_RECEIVABLES, Permission.DELETE_RECEIVABLES,
        Permission.VIEW_PAYABLES, Permission.CREATE_PAYABLES, Permission.EDIT_PAYABLES, Permission.DELETE_PAYABLES,
        Permission.VIEW_INVOICES, Permission.CREATE_INVOICES, Permission.EDIT_INVOICES, Permission.DELETE_INVOICES,
        Permission.VIEW_PAYMENTS, Permission.CREATE_PAYMENTS, Permission.EDIT_PAYMENTS, Permission.DELETE_PAYMENTS,
        Permission.VIEW_SETTLEMENTS, Permission.CREATE_SETTLEMENTS, Permission.EDIT_SETTLEMENTS, Permission.DELETE_SETTLEMENTS,
        # Expenses
        Permission.VIEW_EXPENSES, Permission.CREATE_EXPENSES, Permission.EDIT_EXPENSES, Permission.DELETE_EXPENSES,
    },
    
    # 财务部 - 查看报表、财务记录CRUD、无合同费用CRUD
    UserRole.FINANCE: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
        Permission.DOWNLOAD_REPORTS,
        Permission.VIEW_UPSTREAM_BASIC_INFO,
        Permission.VIEW_DOWNSTREAM_BASIC_INFO,
        Permission.VIEW_MANAGEMENT_BASIC_INFO,
        # All Financial Records
        Permission.VIEW_RECEIVABLES, Permission.CREATE_RECEIVABLES, Permission.EDIT_RECEIVABLES, Permission.DELETE_RECEIVABLES,
        Permission.VIEW_PAYABLES, Permission.CREATE_PAYABLES, Permission.EDIT_PAYABLES, Permission.DELETE_PAYABLES,
        Permission.VIEW_INVOICES, Permission.CREATE_INVOICES, Permission.EDIT_INVOICES, Permission.DELETE_INVOICES,
        Permission.VIEW_PAYMENTS, Permission.CREATE_PAYMENTS, Permission.EDIT_PAYMENTS, Permission.DELETE_PAYMENTS,
        Permission.VIEW_SETTLEMENTS, Permission.CREATE_SETTLEMENTS, Permission.EDIT_SETTLEMENTS, Permission.DELETE_SETTLEMENTS,
        # Expenses
        Permission.VIEW_EXPENSES, Permission.CREATE_EXPENSES, Permission.EDIT_EXPENSES, Permission.DELETE_EXPENSES,
    },
    
    # 工程部 - 查看合同基本信息、应收应付结算CRUD、无合同费用CRUD
    UserRole.ENGINEERING: {
        Permission.VIEW_UPSTREAM_BASIC_INFO,
        Permission.VIEW_DOWNSTREAM_BASIC_INFO,
        Permission.VIEW_MANAGEMENT_BASIC_INFO,
        # Receivables & Payables & Settlements
        Permission.VIEW_RECEIVABLES, Permission.CREATE_RECEIVABLES, Permission.EDIT_RECEIVABLES, Permission.DELETE_RECEIVABLES,
        Permission.VIEW_PAYABLES, Permission.CREATE_PAYABLES, Permission.EDIT_PAYABLES, Permission.DELETE_PAYABLES,
        Permission.VIEW_SETTLEMENTS, Permission.CREATE_SETTLEMENTS, Permission.EDIT_SETTLEMENTS, Permission.DELETE_SETTLEMENTS,
        # Expenses
        Permission.VIEW_EXPENSES, Permission.CREATE_EXPENSES, Permission.EDIT_EXPENSES, Permission.DELETE_EXPENSES,
    },
    
    # 审计部 - 查看合同基本信息、结算记录CRUD、无合同费用CRUD（仅限本人数据）
    UserRole.AUDIT: {
        Permission.VIEW_UPSTREAM_BASIC_INFO,
        Permission.VIEW_DOWNSTREAM_BASIC_INFO,
        Permission.VIEW_MANAGEMENT_BASIC_INFO,
        # Settlements only
        Permission.VIEW_SETTLEMENTS, Permission.CREATE_SETTLEMENTS, Permission.EDIT_SETTLEMENTS, Permission.DELETE_SETTLEMENTS,
        # Expenses (user can only see own data - enforced in service layer)
        Permission.VIEW_EXPENSES, Permission.CREATE_EXPENSES, Permission.EDIT_EXPENSES, Permission.DELETE_EXPENSES,
    },
    
    # 投标部 - 查看上游合同基本信息、无合同费用CRUD（仅限本人数据）
    UserRole.BIDDING: {
        Permission.VIEW_UPSTREAM_BASIC_INFO,
        # Expenses (user can only see own data - enforced in service layer)
        Permission.VIEW_EXPENSES, Permission.CREATE_EXPENSES, Permission.EDIT_EXPENSES, Permission.DELETE_EXPENSES,
    },
    
    # 综合部 - 无合同费用CRUD、管理合同财务记录CRUD
    UserRole.GENERAL_AFFAIRS: {
        Permission.VIEW_MANAGEMENT_BASIC_INFO,
        # Expenses
        Permission.VIEW_EXPENSES, Permission.CREATE_EXPENSES, Permission.EDIT_EXPENSES, Permission.DELETE_EXPENSES,
        # Management Contract Financial Records
        Permission.MANAGE_MGMT_CONTRACT_FINANCE,
        Permission.VIEW_PAYABLES, Permission.CREATE_PAYABLES, Permission.EDIT_PAYABLES, Permission.DELETE_PAYABLES,
        Permission.VIEW_INVOICES, Permission.CREATE_INVOICES, Permission.EDIT_INVOICES, Permission.DELETE_INVOICES,
        Permission.VIEW_PAYMENTS, Permission.CREATE_PAYMENTS, Permission.EDIT_PAYMENTS, Permission.DELETE_PAYMENTS,
        Permission.VIEW_SETTLEMENTS, Permission.CREATE_SETTLEMENTS, Permission.EDIT_SETTLEMENTS, Permission.DELETE_SETTLEMENTS,
    },
}


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has a specific permission"""
    if user.is_superuser:
        return True
    
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions"""
    if user.is_superuser:
        return True
    
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return any(p in user_permissions for p in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """Check if user has all of the specified permissions"""
    if user.is_superuser:
        return True
    
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return all(p in user_permissions for p in permissions)


def get_user_permissions(user: User) -> List[str]:
    """Get list of permission strings for a user"""
    if user.is_superuser:
        return [p.value for p in Permission]
    
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return [p.value for p in user_permissions]


# FastAPI Dependencies for permission checking
def require_permission(permission: Permission):
    """Dependency to require a specific permission"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: 需要 {permission.value} 权限"
            )
        return current_user
    return permission_checker


def require_any_permission(permissions: List[Permission]):
    """Dependency to require any of the specified permissions"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not has_any_permission(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return permission_checker


def require_roles(allowed_roles: List[UserRole]):
    """Dependency to require specific roles"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足: 您的角色无法访问此功能"
            )
        return current_user
    return role_checker
