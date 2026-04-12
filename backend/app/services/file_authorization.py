"""
Authorize access to file-backed business records.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, has_any_permission
from app.models.contract_downstream import (
    ContractDownstream,
    DownstreamSettlement,
    FinanceDownstreamInvoice,
    FinanceDownstreamPayable,
    FinanceDownstreamPayment,
)
from app.models.contract_management import (
    ContractManagement,
    FinanceManagementInvoice,
    FinanceManagementPayable,
    FinanceManagementPayment,
    ManagementSettlement,
)
from app.models.contract_upstream import (
    ContractUpstream,
    FinanceUpstreamInvoice,
    FinanceUpstreamReceipt,
    FinanceUpstreamReceivable,
    ProjectSettlement,
)
from app.models.expense import ExpenseNonContract
from app.models.user import User, UserRole
from app.models.zero_hour_labor import ZeroHourLabor


EXPENSE_VIEW_ALL_ROLES = frozenset(
    {
        UserRole.ADMIN,
        UserRole.CONTRACT_MANAGER,
        UserRole.FINANCE,
    }
)


@dataclass(frozen=True)
class FileAccessRule:
    model: type
    fields: tuple[str, ...]
    permissions: tuple[Permission, ...]
    ownership_field: str | None = None
    view_all_roles: frozenset[UserRole] = frozenset()


FILE_ACCESS_RULES: tuple[FileAccessRule, ...] = (
    FileAccessRule(
        model=ContractUpstream,
        fields=("contract_file_path", "contract_file_key", "approval_pdf_path", "approval_pdf_key"),
        permissions=(Permission.VIEW_UPSTREAM_BASIC_INFO, Permission.VIEW_UPSTREAM_CONTRACTS),
    ),
    FileAccessRule(
        model=FinanceUpstreamReceivable,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_RECEIVABLES,),
    ),
    FileAccessRule(
        model=FinanceUpstreamInvoice,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_INVOICES,),
    ),
    FileAccessRule(
        model=FinanceUpstreamReceipt,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_PAYMENTS,),
    ),
    FileAccessRule(
        model=ProjectSettlement,
        fields=(
            "file_path",
            "file_key",
            "audit_report_path",
            "audit_report_key",
            "start_report_path",
            "start_report_key",
            "completion_report_path",
            "completion_report_key",
        ),
        permissions=(Permission.VIEW_SETTLEMENTS,),
    ),
    FileAccessRule(
        model=ContractDownstream,
        fields=("contract_file_path", "contract_file_key", "approval_pdf_path", "approval_pdf_key"),
        permissions=(Permission.VIEW_DOWNSTREAM_BASIC_INFO, Permission.VIEW_DOWNSTREAM_CONTRACTS),
    ),
    FileAccessRule(
        model=FinanceDownstreamPayable,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_PAYABLES,),
    ),
    FileAccessRule(
        model=FinanceDownstreamInvoice,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_INVOICES,),
    ),
    FileAccessRule(
        model=FinanceDownstreamPayment,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_PAYMENTS,),
    ),
    FileAccessRule(
        model=DownstreamSettlement,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_SETTLEMENTS,),
    ),
    FileAccessRule(
        model=ContractManagement,
        fields=("contract_file_path", "contract_file_key", "approval_pdf_path", "approval_pdf_key"),
        permissions=(Permission.VIEW_MANAGEMENT_BASIC_INFO, Permission.VIEW_MANAGEMENT_CONTRACTS),
    ),
    FileAccessRule(
        model=FinanceManagementPayable,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_PAYABLES,),
    ),
    FileAccessRule(
        model=FinanceManagementInvoice,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_INVOICES,),
    ),
    FileAccessRule(
        model=FinanceManagementPayment,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_PAYMENTS,),
    ),
    FileAccessRule(
        model=ManagementSettlement,
        fields=("file_path", "file_key"),
        permissions=(Permission.VIEW_SETTLEMENTS,),
    ),
    FileAccessRule(
        model=ExpenseNonContract,
        fields=("file_path", "file_key", "approval_pdf_path", "approval_pdf_key"),
        permissions=(Permission.VIEW_EXPENSES,),
        ownership_field="created_by",
        view_all_roles=EXPENSE_VIEW_ALL_ROLES,
    ),
    FileAccessRule(
        model=ZeroHourLabor,
        fields=("dispatch_file_path", "dispatch_file_key", "approval_pdf_path", "approval_pdf_key"),
        permissions=(Permission.VIEW_EXPENSES,),
    ),
)


def normalize_file_reference(path: str) -> str:
    normalized = str(path or "").strip()
    normalized = normalized.split("?", 1)[0]
    normalized = normalized.replace("\\", "/")
    normalized = normalized.lstrip("/")
    if normalized.startswith("uploads/"):
        normalized = normalized[len("uploads/"):]
    return normalized


def _file_reference_candidates(path: str) -> tuple[str, ...]:
    normalized = normalize_file_reference(path)
    if not normalized:
        return tuple()

    return (
        normalized,
        f"/{normalized}",
        f"uploads/{normalized}",
        f"/uploads/{normalized}",
    )


def _record_allows_user(record, rule: FileAccessRule, current_user: User) -> bool:
    if not rule.ownership_field:
        return True
    if current_user.is_superuser or current_user.role in rule.view_all_roles:
        return True
    return getattr(record, rule.ownership_field, None) == current_user.id


async def user_can_access_file_path(path: str, db: AsyncSession, current_user: User) -> bool:
    """
    Allow access only when the file path/key belongs to a known business record the user can view.
    """
    if not current_user:
        return False

    candidates = _file_reference_candidates(path)
    if not candidates:
        return False

    for rule in FILE_ACCESS_RULES:
        if not has_any_permission(current_user, list(rule.permissions)):
            continue

        conditions = [getattr(rule.model, field).in_(candidates) for field in rule.fields]
        result = await db.execute(select(rule.model).where(or_(*conditions)).limit(1))
        record = result.scalar_one_or_none()
        if not record:
            continue
        if _record_allows_user(record, rule, current_user):
            return True

    return False
