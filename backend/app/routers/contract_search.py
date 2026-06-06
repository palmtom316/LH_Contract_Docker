"""
Contract Search Router (合同查询机器人后端)
提供合同模糊搜索和关联信息查询功能
"""
import io
import logging
import urllib.parse
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, and_, cast, String, func
from pydantic import BaseModel

from app.core.permissions import Permission, has_permission
from app.core.errors import PermissionDeniedError
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth import get_current_active_user
from app.models.contract_upstream import (
    ContractUpstream,
    FinanceUpstreamReceivable,
    FinanceUpstreamInvoice,
    FinanceUpstreamReceipt
)
from app.models.contract_downstream import (
    ContractDownstream,
    FinanceDownstreamPayable,
    FinanceDownstreamInvoice,
    FinanceDownstreamPayment
)
from app.models.contract_management import (
    ContractManagement,
    FinanceManagementPayable,
    FinanceManagementInvoice,
    FinanceManagementPayment
)
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor
from app.models.system import SysDictionary

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value) -> float:
    amount = _to_decimal(value)
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


async def _scalar(db: AsyncSession, stmt):
    result = await db.execute(stmt)
    return result.scalar_one() or 0


def _sum_related_amount(items, field: str = "amount") -> Decimal:
    return sum((_to_decimal(getattr(item, field, None)) for item in items), Decimal("0"))


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _build_multi_value_ilike_condition(column, values: list[str]):
    normalized_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = _normalize_text(value)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized_values.append(normalized)

    if not normalized_values:
        return None
    if len(normalized_values) == 1:
        return column.ilike(f"%{normalized_values[0]}%")
    return or_(*[column.ilike(f"%{value}%") for value in normalized_values])


async def _expand_dictionary_filter_values(
    db: AsyncSession,
    *,
    dictionary_category: str,
    raw_value: str,
) -> list[str]:
    normalized = _normalize_text(raw_value)
    if not normalized:
        return []

    stmt = select(SysDictionary).where(
        SysDictionary.category == dictionary_category,
        or_(
            SysDictionary.value == normalized,
            SysDictionary.label == normalized,
        ),
    )
    rows = (await db.execute(stmt)).scalars().all()

    values = [normalized]
    for row in rows:
        values.append(row.value or "")
        values.append(row.label or "")
    return values


def _to_associated_contract(contract, contract_type: str):
    payable_total = _sum_related_amount(contract.payables)
    invoiced_total = _sum_related_amount(contract.invoices)
    paid_total = _sum_related_amount(contract.payments)
    return AssociatedContract(
        id=contract.id,
        serial_number=contract.serial_number,
        contract_code=contract.contract_code,
        contract_name=contract.contract_name,
        party_b_name=contract.party_b_name,
        contract_type=contract_type,
        finance=FinanceSummary(
            contract_amount=_money(contract.contract_amount),
            payable_amount=_money(payable_total),
            invoiced_amount=_money(invoiced_total),
            paid_amount=_money(paid_total)
        )
    )


def _search_scope(user: User) -> dict[str, bool]:
    return {
        "upstream": has_permission(user, Permission.VIEW_UPSTREAM_BASIC_INFO)
        or has_permission(user, Permission.VIEW_UPSTREAM_CONTRACTS),
        "downstream": has_permission(user, Permission.VIEW_DOWNSTREAM_BASIC_INFO)
        or has_permission(user, Permission.VIEW_DOWNSTREAM_CONTRACTS),
        "management": has_permission(user, Permission.VIEW_MANAGEMENT_BASIC_INFO)
        or has_permission(user, Permission.VIEW_MANAGEMENT_CONTRACTS),
        "expenses": has_permission(user, Permission.VIEW_EXPENSES),
    }


def _can_view_all_expenses(user: User) -> bool:
    if user.is_superuser:
        return True
    return user.role in {
        UserRole.ADMIN,
        UserRole.CONTRACT_MANAGER,
        UserRole.FINANCE,
    }


def _apply_upstream_query_filters(
    stmt,
    *,
    keyword: str,
    party_a_name: str,
    contract_category_values: list[str],
    company_category_values: list[str],
    management_mode_values: list[str],
    sign_date_start: Optional[date],
    sign_date_end: Optional[date],
):
    if keyword:
        stmt = stmt.where(
            or_(
                ContractUpstream.contract_code.ilike(f"%{keyword}%"),
                ContractUpstream.contract_name.ilike(f"%{keyword}%"),
                ContractUpstream.party_a_name.ilike(f"%{keyword}%"),
                cast(ContractUpstream.serial_number, String).ilike(f"%{keyword}%"),
            )
        )
    if party_a_name:
        stmt = stmt.where(ContractUpstream.party_a_name.ilike(f"%{party_a_name}%"))
    contract_category_condition = _build_multi_value_ilike_condition(
        ContractUpstream.category,
        contract_category_values,
    )
    if contract_category_condition is not None:
        stmt = stmt.where(contract_category_condition)
    company_category_condition = _build_multi_value_ilike_condition(
        ContractUpstream.company_category,
        company_category_values,
    )
    if company_category_condition is not None:
        stmt = stmt.where(company_category_condition)
    management_mode_condition = _build_multi_value_ilike_condition(
        ContractUpstream.management_mode,
        management_mode_values,
    )
    if management_mode_condition is not None:
        stmt = stmt.where(management_mode_condition)
    if sign_date_start:
        stmt = stmt.where(ContractUpstream.sign_date >= sign_date_start)
    if sign_date_end:
        stmt = stmt.where(ContractUpstream.sign_date <= sign_date_end)
    return stmt


# Response Models
class FinanceSummary(BaseModel):
    """财务汇总"""
    contract_amount: float = 0  # 签约金额
    payable_amount: float = 0   # 应付款
    invoiced_amount: float = 0  # 挂账金额
    paid_amount: float = 0      # 已付款


class AssociatedContract(BaseModel):
    """关联合同"""
    id: int
    serial_number: Optional[int] = None
    contract_code: str
    contract_name: str
    party_b_name: Optional[str] = None
    contract_type: str  # "downstream" or "management"
    finance: FinanceSummary


class ExpenseCategory(BaseModel):
    """费用分类"""
    category: str
    amount: float


class UpstreamContractResult(BaseModel):
    """上游合同查询结果"""
    id: int
    serial_number: Optional[int] = None
    contract_code: str
    contract_name: str
    party_a_name: str
    party_b_name: str
    company_category: Optional[str] = None  # 公司合同分类
    status: Optional[str] = None
    finance: FinanceSummary
    downstream_contracts: List[AssociatedContract] = []
    management_contracts: List[AssociatedContract] = []
    expenses_by_category: List[ExpenseCategory] = []
    
    class Config:
        from_attributes = True


class PartySummary(BaseModel):
    """甲/乙方单位汇总"""
    party_name: str
    contract_count: int = 0
    finance: FinanceSummary


class SearchSummary(BaseModel):
    """搜索汇总"""
    party_a: Optional[PartySummary] = None
    party_b: Optional[PartySummary] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    total: int
    results: List[UpstreamContractResult]
    downstream_results: List[AssociatedContract] = []
    management_results: List[AssociatedContract] = []
    summary: Optional[SearchSummary] = None


class UpstreamAggregateRow(BaseModel):
    id: int
    serial_number: Optional[int] = None
    contract_code: str
    contract_name: str
    party_a_name: str
    party_b_name: str
    category: Optional[str] = None
    company_category: Optional[str] = None
    management_mode: Optional[str] = None
    sign_date: Optional[date] = None
    completion_date: Optional[date] = None
    warranty_date: Optional[date] = None
    contract_amount: float = 0
    receivable_amount: float = 0
    invoiced_amount: float = 0
    received_amount: float = 0
    settlement_amount: float = 0
    downstream_contract_count: int = 0
    downstream_contract_amount: float = 0
    downstream_settlement_amount: float = 0
    downstream_paid_amount: float = 0
    management_contract_count: int = 0
    management_contract_amount: float = 0
    management_settlement_amount: float = 0
    management_paid_amount: float = 0
    non_contract_expense_total: float = 0
    expenses_by_category: List[ExpenseCategory] = []
    zero_hour_labor_total: float = 0


class UpstreamAggregateListResponse(BaseModel):
    total: int
    items: List[UpstreamAggregateRow]
    page: int
    page_size: int


def _sum_contract_field(contracts, field: str) -> Decimal:
    return sum((_to_decimal(getattr(contract, field, None)) for contract in contracts), Decimal("0"))


async def _load_upstream_aggregate_page(
    db: AsyncSession,
    *,
    current_user: User,
    keyword: str,
    party_a_name: str,
    contract_category: str,
    company_category: str,
    management_mode: str,
    sign_date_start: Optional[date],
    sign_date_end: Optional[date],
    page: int = 1,
    page_size: int = 20,
    export_all: bool = False,
):
    scope = _search_scope(current_user)
    if not scope["upstream"]:
        raise PermissionDeniedError()

    contract_category_filters = await _expand_dictionary_filter_values(
        db,
        dictionary_category="contract_category",
        raw_value=contract_category,
    )
    company_category_filters = await _expand_dictionary_filter_values(
        db,
        dictionary_category="project_category",
        raw_value=company_category,
    )
    management_mode_filters = await _expand_dictionary_filter_values(
        db,
        dictionary_category="management_mode",
        raw_value=management_mode,
    )

    count_stmt = _apply_upstream_query_filters(
        select(ContractUpstream.id),
        keyword=keyword,
        party_a_name=party_a_name,
        contract_category_values=contract_category_filters,
        company_category_values=company_category_filters,
        management_mode_values=management_mode_filters,
        sign_date_start=sign_date_start,
        sign_date_end=sign_date_end,
    )
    total = await _scalar(db, select(func.count()).select_from(count_stmt.subquery()))

    stmt = select(ContractUpstream).options(
        selectinload(ContractUpstream.receivables),
        selectinload(ContractUpstream.invoices),
        selectinload(ContractUpstream.receipts),
        selectinload(ContractUpstream.settlements),
    )
    stmt = _apply_upstream_query_filters(
        stmt,
        keyword=keyword,
        party_a_name=party_a_name,
        contract_category_values=contract_category_filters,
        company_category_values=company_category_filters,
        management_mode_values=management_mode_filters,
        sign_date_start=sign_date_start,
        sign_date_end=sign_date_end,
    ).order_by(ContractUpstream.sign_date.desc().nulls_last(), ContractUpstream.id.desc())

    if not export_all:
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    upstream_contracts = (await db.execute(stmt)).scalars().all()
    upstream_ids = [contract.id for contract in upstream_contracts]

    downstream_by_upstream: dict[int, list[ContractDownstream]] = {}
    management_by_upstream: dict[int, list[ContractManagement]] = {}
    expense_total_by_upstream: dict[int, Decimal] = {}
    expense_category_totals_by_upstream: dict[int, dict[str, Decimal]] = {}
    labor_total_by_upstream: dict[int, Decimal] = {}

    if upstream_ids and scope["downstream"]:
        downstream_stmt = select(ContractDownstream).options(
            selectinload(ContractDownstream.payments),
            selectinload(ContractDownstream.settlements),
        ).where(ContractDownstream.upstream_contract_id.in_(upstream_ids))
        downstream_rows = (await db.execute(downstream_stmt)).scalars().all()
        for row in downstream_rows:
            downstream_by_upstream.setdefault(row.upstream_contract_id, []).append(row)

    if upstream_ids and scope["management"]:
        management_stmt = select(ContractManagement).options(
            selectinload(ContractManagement.payments),
            selectinload(ContractManagement.settlements),
        ).where(ContractManagement.upstream_contract_id.in_(upstream_ids))
        management_rows = (await db.execute(management_stmt)).scalars().all()
        for row in management_rows:
            management_by_upstream.setdefault(row.upstream_contract_id, []).append(row)

    if upstream_ids and scope["expenses"]:
        expense_stmt = select(ExpenseNonContract).where(
            ExpenseNonContract.upstream_contract_id.in_(upstream_ids)
        )
        labor_stmt = select(ZeroHourLabor).where(
            ZeroHourLabor.upstream_contract_id.in_(upstream_ids)
        )
        if not _can_view_all_expenses(current_user):
            expense_stmt = expense_stmt.where(ExpenseNonContract.created_by == current_user.id)
            labor_stmt = labor_stmt.where(ZeroHourLabor.created_by == current_user.id)

        expense_rows = (await db.execute(expense_stmt)).scalars().all()
        for row in expense_rows:
            expense_total_by_upstream[row.upstream_contract_id] = (
                expense_total_by_upstream.get(row.upstream_contract_id, Decimal("0"))
                + _to_decimal(row.amount)
            )
            category_label = row.expense_type or row.category or "未分类"
            category_totals = expense_category_totals_by_upstream.setdefault(row.upstream_contract_id, {})
            category_totals[category_label] = category_totals.get(category_label, Decimal("0")) + _to_decimal(row.amount)

        labor_rows = (await db.execute(labor_stmt)).scalars().all()
        for row in labor_rows:
            labor_total_by_upstream[row.upstream_contract_id] = (
                labor_total_by_upstream.get(row.upstream_contract_id, Decimal("0"))
                + _to_decimal(row.total_amount)
            )

    items: List[UpstreamAggregateRow] = []
    for upstream in upstream_contracts:
        downstream_rows = downstream_by_upstream.get(upstream.id, [])
        management_rows = management_by_upstream.get(upstream.id, [])
        latest_settlement = upstream.latest_settlement
        expense_category_rows = [
            ExpenseCategory(category=category, amount=_money(amount))
            for category, amount in sorted(
                expense_category_totals_by_upstream.get(upstream.id, {}).items(),
                key=lambda item: item[0],
            )
        ]
        items.append(
            UpstreamAggregateRow(
                id=upstream.id,
                serial_number=upstream.serial_number,
                contract_code=upstream.contract_code,
                contract_name=upstream.contract_name,
                party_a_name=upstream.party_a_name,
                party_b_name=upstream.party_b_name,
                category=upstream.category,
                company_category=upstream.company_category,
                management_mode=upstream.management_mode,
                sign_date=upstream.sign_date,
                completion_date=latest_settlement.completion_date if latest_settlement else None,
                warranty_date=latest_settlement.warranty_date if latest_settlement else None,
                contract_amount=_money(upstream.contract_amount),
                receivable_amount=_money(_sum_related_amount(upstream.receivables)),
                invoiced_amount=_money(_sum_related_amount(upstream.invoices)),
                received_amount=_money(_sum_related_amount(upstream.receipts)),
                settlement_amount=_money(_sum_related_amount(upstream.settlements, field="settlement_amount")),
                downstream_contract_count=len(downstream_rows),
                downstream_contract_amount=_money(_sum_contract_field(downstream_rows, "contract_amount")),
                downstream_settlement_amount=_money(_sum_contract_field(downstream_rows, "total_settlement")),
                downstream_paid_amount=_money(_sum_contract_field(downstream_rows, "total_paid")),
                management_contract_count=len(management_rows),
                management_contract_amount=_money(_sum_contract_field(management_rows, "contract_amount")),
                management_settlement_amount=_money(_sum_contract_field(management_rows, "total_settlement")),
                management_paid_amount=_money(_sum_contract_field(management_rows, "total_paid")),
                non_contract_expense_total=_money(expense_total_by_upstream.get(upstream.id, Decimal("0"))),
                expenses_by_category=expense_category_rows,
                zero_hour_labor_total=_money(labor_total_by_upstream.get(upstream.id, Decimal("0"))),
            )
        )

    return total, items


@router.get("/search/upstream-query", response_model=UpstreamAggregateListResponse)
async def query_upstream_contracts(
    keyword: str = Query("", description="搜索关键词（合同序号、名称或编号）"),
    party_a_name: str = Query("", description="甲方单位"),
    contract_category: str = Query("", description="合同类别"),
    company_category: str = Query("", description="合同公司分类"),
    management_mode: str = Query("", description="管理模式"),
    sign_date_start: Optional[date] = Query(None, description="签约开始日期"),
    sign_date_end: Optional[date] = Query(None, description="签约结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    total, items = await _load_upstream_aggregate_page(
        db,
        current_user=current_user,
        keyword=_normalize_text(keyword),
        party_a_name=_normalize_text(party_a_name),
        contract_category=_normalize_text(contract_category),
        company_category=_normalize_text(company_category),
        management_mode=_normalize_text(management_mode),
        sign_date_start=sign_date_start,
        sign_date_end=sign_date_end,
        page=page,
        page_size=page_size,
    )
    return UpstreamAggregateListResponse(
        total=int(total),
        items=items,
        page=page,
        page_size=page_size,
    )


@router.get("/search/upstream-query/export")
async def export_upstream_contract_query(
    keyword: str = Query("", description="搜索关键词（合同序号、名称或编号）"),
    party_a_name: str = Query("", description="甲方单位"),
    contract_category: str = Query("", description="合同类别"),
    company_category: str = Query("", description="合同公司分类"),
    management_mode: str = Query("", description="管理模式"),
    sign_date_start: Optional[date] = Query(None, description="签约开始日期"),
    sign_date_end: Optional[date] = Query(None, description="签约结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _, items = await _load_upstream_aggregate_page(
        db,
        current_user=current_user,
        keyword=_normalize_text(keyword),
        party_a_name=_normalize_text(party_a_name),
        contract_category=_normalize_text(contract_category),
        company_category=_normalize_text(company_category),
        management_mode=_normalize_text(management_mode),
        sign_date_start=sign_date_start,
        sign_date_end=sign_date_end,
        export_all=True,
    )

    export_rows = [
        {
            "合同名称": row.contract_name,
            "甲方单位": row.party_a_name,
            "乙方单位": row.party_b_name,
            "合同类别": row.category or "",
            "合同公司分类": row.company_category or "",
            "管理模式": row.management_mode or "",
            "签约金额": row.contract_amount,
            "签约日期": row.sign_date.isoformat() if row.sign_date else "",
            "完工日期": row.completion_date.isoformat() if row.completion_date else "",
            "质保到期日期": row.warranty_date.isoformat() if row.warranty_date else "",
            "应收款": row.receivable_amount,
            "挂账金额": row.invoiced_amount,
            "已收款": row.received_amount,
            "结算金额": row.settlement_amount,
            "关联下游合同个数": row.downstream_contract_count,
            "关联下游合同签约总金额": row.downstream_contract_amount,
            "关联下游合同结算总金额": row.downstream_settlement_amount,
            "关联下游合同已付款总金额": row.downstream_paid_amount,
            "关联管理合同个数": row.management_contract_count,
            "关联管理合同签约总金额": row.management_contract_amount,
            "关联管理合同结算总金额": row.management_settlement_amount,
            "关联管理合同已付款总金额": row.management_paid_amount,
            "关联无合同费用总金额": row.non_contract_expense_total,
            "关联无合同费用分类汇总": "；".join(
                f"{item.category}: {item.amount:.2f}" for item in row.expenses_by_category
            ),
            "关联零星用工总金额": row.zero_hour_labor_total,
        }
        for row in items
    ]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(export_rows).to_excel(writer, index=False, sheet_name="上游合同查询")
    output.seek(0)

    filename = f"上游合同查询_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"},
    )


@router.get("/search", response_model=SearchResponse)
async def search_contracts(
    query: str = Query("", description="搜索关键词（合同序号、名称或编号）"),
    company_category: str = Query("", description="公司合同分类"),
    party_a_name: str = Query("", description="上游合同甲方单位"),
    party_b_name: str = Query("", description="下游/管理合同乙方单位"),
    sign_date_start: Optional[date] = Query(None, description="签约时间开始日期（YYYY-MM-DD）"),
    sign_date_end: Optional[date] = Query(None, description="签约时间结束日期（YYYY-MM-DD）"),
    limit: Optional[int] = Query(None, ge=1, le=5000, description="返回结果数量限制（为空不限制）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    模糊查询上游合同及其关联的下游合同、管理合同和无合同费用
    
    Args:
        query: 搜索关键词，支持合同序号、合同名称或合同编号模糊匹配
        company_category: 公司合同分类筛选
        party_a_name: 上游合同甲方单位模糊匹配
        party_b_name: 下游/管理合同乙方单位模糊匹配
        sign_date_start: 签约时间起始日期
        sign_date_end: 签约时间结束日期
        limit: 返回结果数量限制（为空不限制）
        
    Returns:
        匹配的上游合同列表，包含财务汇总和关联合同信息
    """
    scope = _search_scope(current_user)
    if not any(scope.values()):
        raise PermissionDeniedError()

    # Normalize inputs
    query = (query or "").strip()
    company_category = (company_category or "").strip()
    party_a_name = (party_a_name or "").strip()
    party_b_name = (party_b_name or "").strip()
    has_party_a = bool(party_a_name)
    has_party_b = bool(party_b_name)
    has_sign_date_filter = bool(sign_date_start or sign_date_end)
    has_any = bool(query or company_category or party_a_name or party_b_name or has_sign_date_filter)

    # Build upstream query conditions
    upstream_conditions = []
    
    # Text search condition (query)
    if query:
        upstream_conditions.append(
            or_(
                ContractUpstream.contract_code.ilike(f"%{query}%"),
                ContractUpstream.contract_name.ilike(f"%{query}%"),
                cast(ContractUpstream.serial_number, String).ilike(f"%{query}%")
            )
        )
    
    # Company category filter
    if company_category:
        upstream_conditions.append(ContractUpstream.company_category.ilike(f"%{company_category}%"))

    # Party A filter (Upstream)
    if has_party_a:
        upstream_conditions.append(ContractUpstream.party_a_name.ilike(f"%{party_a_name}%"))

    # Sign date range filter (Upstream)
    if sign_date_start:
        upstream_conditions.append(ContractUpstream.sign_date >= sign_date_start)
    if sign_date_end:
        upstream_conditions.append(ContractUpstream.sign_date <= sign_date_end)
    
    # At least one condition is required
    if not has_any:
        return SearchResponse(total=0, results=[], summary=None)

    upstream_filter = and_(*upstream_conditions) if upstream_conditions else None
    show_upstream_results = scope["upstream"] and not has_party_b
    upstream_ids_subq = None
    if show_upstream_results and upstream_filter is not None:
        upstream_ids_subq = select(ContractUpstream.id).where(upstream_filter).subquery()

    upstream_total = 0
    if show_upstream_results and upstream_filter is not None:
        upstream_total = await _scalar(
            db,
            select(func.count()).select_from(ContractUpstream).where(upstream_filter)
        )

    results = []
    if show_upstream_results and upstream_filter is not None:
        # Query upstream contracts with fuzzy matching
        stmt = select(ContractUpstream).options(
            selectinload(ContractUpstream.receivables),
            selectinload(ContractUpstream.invoices),
            selectinload(ContractUpstream.receipts),
            selectinload(ContractUpstream.settlements)
        ).where(upstream_filter).order_by(ContractUpstream.serial_number.desc().nulls_last())
        if limit:
            stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        upstream_contracts = result.scalars().all()
    else:
        upstream_contracts = []

    upstream_ids = [up.id for up in upstream_contracts]
    downstream_by_upstream: dict[int, list[ContractDownstream]] = {}
    management_by_upstream: dict[int, list[ContractManagement]] = {}
    expense_summary_by_upstream: dict[int, dict[str, Decimal]] = {}

    if upstream_ids and scope["downstream"]:
        stmt_down = select(ContractDownstream).options(
            selectinload(ContractDownstream.payables),
            selectinload(ContractDownstream.invoices),
            selectinload(ContractDownstream.payments),
            selectinload(ContractDownstream.settlements)
        ).where(ContractDownstream.upstream_contract_id.in_(upstream_ids))
        res_down = await db.execute(stmt_down)
        for downstream in res_down.scalars().all():
            downstream_by_upstream.setdefault(downstream.upstream_contract_id, []).append(downstream)

    if upstream_ids and scope["management"]:
        stmt_mgmt = select(ContractManagement).options(
            selectinload(ContractManagement.payables),
            selectinload(ContractManagement.invoices),
            selectinload(ContractManagement.payments),
            selectinload(ContractManagement.settlements)
        ).where(ContractManagement.upstream_contract_id.in_(upstream_ids))
        res_mgmt = await db.execute(stmt_mgmt)
        for management in res_mgmt.scalars().all():
            management_by_upstream.setdefault(management.upstream_contract_id, []).append(management)
    
    # Expense type translation mapping
    expense_type_map = {
        "MANAGEMENT": "管理费",
        "TRAINING": "培训费",
        "CATERING": "餐饮费",
        "TRANSPORT": "交通费",
        "CONSULTING": "咨询费",
        "BUSINESS": "业务费",
        "LEASING": "租赁费",
        "QUALIFICATION": "资质费",
        "VEHICLE": "车辆使用费"
    }

    if upstream_ids and scope["expenses"]:
        stmt_exp = select(ExpenseNonContract).where(
            ExpenseNonContract.upstream_contract_id.in_(upstream_ids)
        )
        stmt_zhl = select(ZeroHourLabor).where(
            ZeroHourLabor.upstream_contract_id.in_(upstream_ids)
        )
        if not _can_view_all_expenses(current_user):
            stmt_exp = stmt_exp.where(ExpenseNonContract.created_by == current_user.id)
            stmt_zhl = stmt_zhl.where(ZeroHourLabor.created_by == current_user.id)

        res_exp = await db.execute(stmt_exp)
        for expense in res_exp.scalars().all():
            contract_summary = expense_summary_by_upstream.setdefault(expense.upstream_contract_id, {})
            expense_type = expense.expense_type or "未分类"
            category_name = expense_type_map.get(expense_type, expense_type)
            contract_summary[category_name] = contract_summary.get(category_name, Decimal("0")) + _to_decimal(expense.amount)

        res_zhl = await db.execute(stmt_zhl)
        for labor in res_zhl.scalars().all():
            contract_summary = expense_summary_by_upstream.setdefault(labor.upstream_contract_id, {})
            contract_summary["零星用工"] = contract_summary.get("零星用工", Decimal("0")) + _to_decimal(labor.total_amount)
    
    for up in upstream_contracts:
        # Calculate upstream finance summary
        # 应收款 = sum of receivables
        receivable_total = _sum_related_amount(up.receivables)
        # 挂账金额 = sum of invoices
        invoiced_total = _sum_related_amount(up.invoices)
        # 已收款 = sum of receipts
        received_total = _sum_related_amount(up.receipts)
        
        up_finance = FinanceSummary(
            contract_amount=_money(up.contract_amount),
            payable_amount=_money(receivable_total),  # 对于上游合同，应收款 = 应付方的应付
            invoiced_amount=_money(invoiced_total),
            paid_amount=_money(received_total)
        )
        
        downstream_list = []
        if scope["downstream"]:
            downstream_list = [
                _to_associated_contract(downstream, "downstream")
                for downstream in downstream_by_upstream.get(up.id, [])
            ]

        management_list = []
        if scope["management"]:
            management_list = [
                _to_associated_contract(management, "management")
                for management in management_by_upstream.get(up.id, [])
            ]

        expenses_list = []
        if scope["expenses"]:
            expenses_list = [
                ExpenseCategory(category=cat, amount=_money(amt))
                for cat, amt in expense_summary_by_upstream.get(up.id, {}).items()
            ]
        
        results.append(UpstreamContractResult(
            id=up.id,
            serial_number=up.serial_number,
            contract_code=up.contract_code,
            contract_name=up.contract_name,
            party_a_name=up.party_a_name,
            party_b_name=up.party_b_name,
            company_category=up.company_category,
            status=up.status,
            finance=up_finance,
            downstream_contracts=downstream_list,
            management_contracts=management_list,
            expenses_by_category=expenses_list
        ))
    
    downstream_results: List[AssociatedContract] = []
    management_results: List[AssociatedContract] = []
    downstream_ids_subq = None
    management_ids_subq = None
    downstream_count = 0
    management_count = 0

    if has_party_b:
        if scope["downstream"]:
            downstream_conditions = [
                ContractDownstream.party_b_name.ilike(f"%{party_b_name}%")
            ]
            if query:
                downstream_conditions.append(
                    or_(
                        ContractDownstream.contract_code.ilike(f"%{query}%"),
                        ContractDownstream.contract_name.ilike(f"%{query}%"),
                        cast(ContractDownstream.serial_number, String).ilike(f"%{query}%")
                    )
                )
            if sign_date_start:
                downstream_conditions.append(ContractDownstream.sign_date >= sign_date_start)
            if sign_date_end:
                downstream_conditions.append(ContractDownstream.sign_date <= sign_date_end)

            downstream_ids_subq = select(ContractDownstream.id).where(and_(*downstream_conditions)).subquery()
            downstream_count = await _scalar(db, select(func.count()).select_from(downstream_ids_subq))

            stmt_down_results = select(ContractDownstream).options(
                selectinload(ContractDownstream.payables),
                selectinload(ContractDownstream.invoices),
                selectinload(ContractDownstream.payments),
                selectinload(ContractDownstream.settlements)
            ).where(ContractDownstream.id.in_(select(downstream_ids_subq.c.id)))
            if limit:
                stmt_down_results = stmt_down_results.limit(limit)
            res_down = await db.execute(stmt_down_results)
            downs = res_down.scalars().all()
            for d in downs:
                downstream_results.append(_to_associated_contract(d, "downstream"))

        if scope["management"]:
            management_conditions = [
                ContractManagement.party_b_name.ilike(f"%{party_b_name}%")
            ]
            if query:
                management_conditions.append(
                    or_(
                        ContractManagement.contract_code.ilike(f"%{query}%"),
                        ContractManagement.contract_name.ilike(f"%{query}%"),
                        cast(ContractManagement.serial_number, String).ilike(f"%{query}%")
                    )
                )
            if sign_date_start:
                management_conditions.append(ContractManagement.sign_date >= sign_date_start)
            if sign_date_end:
                management_conditions.append(ContractManagement.sign_date <= sign_date_end)

            management_ids_subq = select(ContractManagement.id).where(and_(*management_conditions)).subquery()
            management_count = await _scalar(db, select(func.count()).select_from(management_ids_subq))

            stmt_mgmt_results = select(ContractManagement).options(
                selectinload(ContractManagement.payables),
                selectinload(ContractManagement.invoices),
                selectinload(ContractManagement.payments),
                selectinload(ContractManagement.settlements)
            ).where(ContractManagement.id.in_(select(management_ids_subq.c.id)))
            if limit:
                stmt_mgmt_results = stmt_mgmt_results.limit(limit)
            res_mgmt = await db.execute(stmt_mgmt_results)
            mgmts = res_mgmt.scalars().all()
            for m in mgmts:
                management_results.append(_to_associated_contract(m, "management"))

    summary = None
    if show_upstream_results and upstream_filter is not None:
        contract_amount_sum = await _scalar(
            db,
            select(func.coalesce(func.sum(ContractUpstream.contract_amount), 0)).where(upstream_filter)
        )
        receivable_sum = await _scalar(
            db,
            select(func.coalesce(func.sum(FinanceUpstreamReceivable.amount), 0)).where(
                FinanceUpstreamReceivable.contract_id.in_(select(upstream_ids_subq.c.id))
            )
        ) if upstream_ids_subq is not None else 0
        invoiced_sum = await _scalar(
            db,
            select(func.coalesce(func.sum(FinanceUpstreamInvoice.amount), 0)).where(
                FinanceUpstreamInvoice.contract_id.in_(select(upstream_ids_subq.c.id))
            )
        ) if upstream_ids_subq is not None else 0
        received_sum = await _scalar(
            db,
            select(func.coalesce(func.sum(FinanceUpstreamReceipt.amount), 0)).where(
                FinanceUpstreamReceipt.contract_id.in_(select(upstream_ids_subq.c.id))
            )
        ) if upstream_ids_subq is not None else 0
        summary = SearchSummary(
            party_a=PartySummary(
                party_name=party_a_name or "上游合同汇总",
                contract_count=int(upstream_total),
                finance=FinanceSummary(
                    contract_amount=_money(contract_amount_sum),
                    payable_amount=_money(receivable_sum),
                    invoiced_amount=_money(invoiced_sum),
                    paid_amount=_money(received_sum)
                )
            )
        )

    if has_party_b and (downstream_ids_subq is not None or management_ids_subq is not None):
        down_contract_sum = 0
        mgmt_contract_sum = 0
        down_payable_sum = 0
        mgmt_payable_sum = 0
        down_invoiced_sum = 0
        mgmt_invoiced_sum = 0
        down_paid_sum = 0
        mgmt_paid_sum = 0

        if downstream_ids_subq is not None:
            down_contract_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(ContractDownstream.contract_amount), 0)).where(
                    ContractDownstream.id.in_(select(downstream_ids_subq.c.id))
                )
            )
            down_payable_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(FinanceDownstreamPayable.amount), 0)).where(
                    FinanceDownstreamPayable.contract_id.in_(select(downstream_ids_subq.c.id))
                )
            )
            down_invoiced_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(FinanceDownstreamInvoice.amount), 0)).where(
                    FinanceDownstreamInvoice.contract_id.in_(select(downstream_ids_subq.c.id))
                )
            )
            down_paid_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(FinanceDownstreamPayment.amount), 0)).where(
                    FinanceDownstreamPayment.contract_id.in_(select(downstream_ids_subq.c.id))
                )
            )

        if management_ids_subq is not None:
            mgmt_contract_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(ContractManagement.contract_amount), 0)).where(
                    ContractManagement.id.in_(select(management_ids_subq.c.id))
                )
            )
            mgmt_payable_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(FinanceManagementPayable.amount), 0)).where(
                    FinanceManagementPayable.contract_id.in_(select(management_ids_subq.c.id))
                )
            )
            mgmt_invoiced_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(FinanceManagementInvoice.amount), 0)).where(
                    FinanceManagementInvoice.contract_id.in_(select(management_ids_subq.c.id))
                )
            )
            mgmt_paid_sum = await _scalar(
                db,
                select(func.coalesce(func.sum(FinanceManagementPayment.amount), 0)).where(
                    FinanceManagementPayment.contract_id.in_(select(management_ids_subq.c.id))
                )
            )

        party_b_summary = PartySummary(
            party_name=party_b_name or "乙方单位汇总",
            contract_count=int(downstream_count + management_count),
            finance=FinanceSummary(
                contract_amount=_money(_to_decimal(down_contract_sum) + _to_decimal(mgmt_contract_sum)),
                payable_amount=_money(_to_decimal(down_payable_sum) + _to_decimal(mgmt_payable_sum)),
                invoiced_amount=_money(_to_decimal(down_invoiced_sum) + _to_decimal(mgmt_invoiced_sum)),
                paid_amount=_money(_to_decimal(down_paid_sum) + _to_decimal(mgmt_paid_sum))
            )
        )
        if summary:
            summary.party_b = party_b_summary
        else:
            summary = SearchSummary(party_b=party_b_summary)

    total = int(upstream_total)
    if has_party_b:
        total = int(downstream_count + management_count)

    return SearchResponse(
        total=total,
        results=results,
        downstream_results=downstream_results,
        management_results=management_results,
        summary=summary
    )
