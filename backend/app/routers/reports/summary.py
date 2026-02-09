"""
Reports Module - Summary Statistics and Cache Management
Extracted from monolithic reports.py for better maintainability
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, cast, Integer
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

from app.database import get_db
from app.models.user import User
from app.models.system import SysDictionary
from app.models.contract_upstream import (
    ContractUpstream,
    FinanceUpstreamReceipt,
    FinanceUpstreamReceivable,
    FinanceUpstreamInvoice,
    ProjectSettlement,
)
from app.models.contract_downstream import (
    ContractDownstream,
    FinanceDownstreamPayment,
    FinanceDownstreamPayable,
    FinanceDownstreamInvoice,
    DownstreamSettlement,
)
from app.models.contract_management import (
    ContractManagement,
    FinanceManagementPayment,
    FinanceManagementPayable,
    FinanceManagementInvoice,
    ManagementSettlement,
)
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor
from app.services.auth import get_current_active_user
from app.core.permissions import require_permission, Permission
from app.services.report_cache import (
    get_cached_report, 
    set_cached_report,
    invalidate_report_cache
)

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_permission(Permission.VIEW_REPORTS))])

_COST_METRIC_KEYS = [
    "upstream_contract_amount",
    "upstream_receivable",
    "upstream_invoice",
    "upstream_receipt",
    "upstream_settlement",
    "down_mgmt_contract_amount",
    "down_mgmt_payable",
    "down_mgmt_invoice",
    "down_mgmt_payment",
    "down_mgmt_settlement",
    "zero_hour_labor",
    "non_contract_expense",
]


def _period_filters(column, year: int, months: List[int]):
    filters = [cast(extract("year", column), Integer) == year]
    if len(months) == 1:
        filters.append(cast(extract("month", column), Integer) == months[0])
    else:
        filters.append(cast(extract("month", column), Integer).in_(months))
    return filters


async def _execute_group_sum(db: AsyncSession, stmt) -> Dict[str, float]:
    result = await db.execute(stmt)
    grouped: Dict[str, float] = {}
    for category, amount in result.all():
        key = category or "未分类"
        grouped[key] = grouped.get(key, 0.0) + float(amount or 0)
    return grouped


def _merge_amounts(base: Dict[str, float], extra: Dict[str, float]) -> Dict[str, float]:
    merged = dict(base)
    for key, value in extra.items():
        merged[key] = merged.get(key, 0.0) + float(value or 0)
    return merged


async def _get_project_category_order(db: AsyncSession) -> List[str]:
    stmt = (
        select(SysDictionary.value)
        .where(
            SysDictionary.category == "project_category",
            SysDictionary.is_active == True,  # noqa: E712
        )
        .order_by(SysDictionary.sort_order, SysDictionary.id)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all() if row[0]]


async def _collect_cost_metrics(
    db: AsyncSession,
    year: int,
    months: List[int],
) -> Tuple[Dict[str, Dict[str, float]], set]:
    metrics: Dict[str, Dict[str, float]] = {}

    metrics["upstream_contract_amount"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ContractUpstream.contract_amount),
        )
        .where(*_period_filters(ContractUpstream.sign_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    metrics["upstream_receivable"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceUpstreamReceivable.amount),
        )
        .select_from(FinanceUpstreamReceivable)
        .join(ContractUpstream, FinanceUpstreamReceivable.contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceUpstreamReceivable.expected_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    metrics["upstream_invoice"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceUpstreamInvoice.amount),
        )
        .select_from(FinanceUpstreamInvoice)
        .join(ContractUpstream, FinanceUpstreamInvoice.contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceUpstreamInvoice.invoice_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    metrics["upstream_receipt"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceUpstreamReceipt.amount),
        )
        .select_from(FinanceUpstreamReceipt)
        .join(ContractUpstream, FinanceUpstreamReceipt.contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceUpstreamReceipt.receipt_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    metrics["upstream_settlement"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ProjectSettlement.settlement_amount),
        )
        .select_from(ProjectSettlement)
        .join(ContractUpstream, ProjectSettlement.contract_id == ContractUpstream.id)
        .where(*_period_filters(ProjectSettlement.settlement_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    down_contract = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ContractDownstream.contract_amount),
        )
        .select_from(ContractDownstream)
        .outerjoin(ContractUpstream, ContractDownstream.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(ContractDownstream.sign_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    mgmt_contract = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ContractManagement.contract_amount),
        )
        .select_from(ContractManagement)
        .outerjoin(ContractUpstream, ContractManagement.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(ContractManagement.sign_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    metrics["down_mgmt_contract_amount"] = _merge_amounts(down_contract, mgmt_contract)

    down_payable = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceDownstreamPayable.amount),
        )
        .select_from(FinanceDownstreamPayable)
        .join(ContractDownstream, FinanceDownstreamPayable.contract_id == ContractDownstream.id)
        .outerjoin(ContractUpstream, ContractDownstream.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceDownstreamPayable.expected_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    mgmt_payable = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceManagementPayable.amount),
        )
        .select_from(FinanceManagementPayable)
        .join(ContractManagement, FinanceManagementPayable.contract_id == ContractManagement.id)
        .outerjoin(ContractUpstream, ContractManagement.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceManagementPayable.expected_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    metrics["down_mgmt_payable"] = _merge_amounts(down_payable, mgmt_payable)

    down_invoice = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceDownstreamInvoice.amount),
        )
        .select_from(FinanceDownstreamInvoice)
        .join(ContractDownstream, FinanceDownstreamInvoice.contract_id == ContractDownstream.id)
        .outerjoin(ContractUpstream, ContractDownstream.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceDownstreamInvoice.invoice_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    mgmt_invoice = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceManagementInvoice.amount),
        )
        .select_from(FinanceManagementInvoice)
        .join(ContractManagement, FinanceManagementInvoice.contract_id == ContractManagement.id)
        .outerjoin(ContractUpstream, ContractManagement.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceManagementInvoice.invoice_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    metrics["down_mgmt_invoice"] = _merge_amounts(down_invoice, mgmt_invoice)

    down_payment = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceDownstreamPayment.amount),
        )
        .select_from(FinanceDownstreamPayment)
        .join(ContractDownstream, FinanceDownstreamPayment.contract_id == ContractDownstream.id)
        .outerjoin(ContractUpstream, ContractDownstream.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceDownstreamPayment.payment_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    mgmt_payment = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(FinanceManagementPayment.amount),
        )
        .select_from(FinanceManagementPayment)
        .join(ContractManagement, FinanceManagementPayment.contract_id == ContractManagement.id)
        .outerjoin(ContractUpstream, ContractManagement.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(FinanceManagementPayment.payment_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    metrics["down_mgmt_payment"] = _merge_amounts(down_payment, mgmt_payment)

    down_settlement = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(DownstreamSettlement.settlement_amount),
        )
        .select_from(DownstreamSettlement)
        .join(ContractDownstream, DownstreamSettlement.contract_id == ContractDownstream.id)
        .outerjoin(ContractUpstream, ContractDownstream.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(DownstreamSettlement.settlement_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    mgmt_settlement = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ManagementSettlement.settlement_amount),
        )
        .select_from(ManagementSettlement)
        .join(ContractManagement, ManagementSettlement.contract_id == ContractManagement.id)
        .outerjoin(ContractUpstream, ContractManagement.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(ManagementSettlement.settlement_date, year, months))
        .group_by(ContractUpstream.company_category),
    )
    metrics["down_mgmt_settlement"] = _merge_amounts(down_settlement, mgmt_settlement)

    metrics["zero_hour_labor"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ZeroHourLabor.total_amount),
        )
        .select_from(ZeroHourLabor)
        .outerjoin(ContractUpstream, ZeroHourLabor.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(ZeroHourLabor.labor_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    metrics["non_contract_expense"] = await _execute_group_sum(
        db,
        select(
            ContractUpstream.company_category,
            func.sum(ExpenseNonContract.amount),
        )
        .select_from(ExpenseNonContract)
        .outerjoin(ContractUpstream, ExpenseNonContract.upstream_contract_id == ContractUpstream.id)
        .where(*_period_filters(ExpenseNonContract.expense_date, year, months))
        .group_by(ContractUpstream.company_category),
    )

    categories_found = set()
    for value_map in metrics.values():
        categories_found.update(value_map.keys())

    return metrics, categories_found


def _build_rows_and_total(
    categories: List[str],
    metrics: Dict[str, Dict[str, float]],
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    rows = []
    total = {"company_category": "合计"}
    for key in _COST_METRIC_KEYS:
        total[key] = 0.0

    for category in categories:
        row = {"company_category": category}
        for key in _COST_METRIC_KEYS:
            value = float(metrics.get(key, {}).get(category, 0.0))
            row[key] = value
            total[key] += value
        rows.append(row)

    return rows, total


def _get_cost_period_context(month: int) -> Dict[str, object]:
    quarter = (month - 1) // 3 + 1
    quarter_months = [3 * (quarter - 1) + 1, 3 * (quarter - 1) + 2, 3 * (quarter - 1) + 3]
    half_year = 1 if month <= 6 else 2
    half_year_months = [1, 2, 3, 4, 5, 6] if half_year == 1 else [7, 8, 9, 10, 11, 12]
    year_months = list(range(1, 13))
    return {
        "quarter": quarter,
        "quarter_months": quarter_months,
        "half_year": half_year,
        "half_year_months": half_year_months,
        "year_months": year_months,
    }


async def _build_cost_report_payload(db: AsyncSession, year: int, month: int) -> Dict[str, object]:
    period_ctx = _get_cost_period_context(month)
    quarter_months = period_ctx["quarter_months"]
    half_year_months = period_ctx["half_year_months"]
    year_months = period_ctx["year_months"]

    month_metrics, month_categories = await _collect_cost_metrics(db, year, [month])
    quarter_metrics, quarter_categories = await _collect_cost_metrics(db, year, quarter_months)
    half_year_metrics, half_year_categories = await _collect_cost_metrics(db, year, half_year_months)
    year_metrics, year_categories = await _collect_cost_metrics(db, year, year_months)

    dict_categories = await _get_project_category_order(db)
    categories_found = month_categories | quarter_categories | half_year_categories | year_categories
    extra_categories = sorted(categories_found - set(dict_categories))
    categories = dict_categories + extra_categories

    monthly_rows, monthly_total = _build_rows_and_total(categories, month_metrics)
    quarterly_rows, quarterly_total = _build_rows_and_total(categories, quarter_metrics)
    half_yearly_rows, half_yearly_total = _build_rows_and_total(categories, half_year_metrics)
    yearly_rows, yearly_total = _build_rows_and_total(categories, year_metrics)

    return {
        "period": {
            "year": year,
            "month": month,
            "quarter": period_ctx["quarter"],
            "quarter_months": quarter_months,
            "half_year": period_ctx["half_year"],
            "half_year_months": half_year_months,
            "year_months": year_months,
        },
        "monthly": {
            "rows": monthly_rows,
            "total": monthly_total,
        },
        "quarterly": {
            "rows": quarterly_rows,
            "total": quarterly_total,
        },
        "half_yearly": {
            "rows": half_yearly_rows,
            "total": half_yearly_total,
        },
        "yearly": {
            "rows": yearly_rows,
            "total": yearly_total,
        },
    }


@router.post("/cache/invalidate")
async def invalidate_cache(
    report_type: str = None,
    year: int = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Invalidate report cache. Admin only.
    """
    from app.core.errors import PermissionDeniedError
    if not current_user.is_superuser and current_user.role.value != "ADMIN":
        raise PermissionDeniedError(
            message="只有管理员可以清除缓存",
            detail="需要管理员权限"
        )
    
    count = await invalidate_report_cache(report_type, year)
    
    return {
        "success": True,
        "message": f"已清除 {count} 条缓存记录",
        "invalidated_count": count
    }


@router.get("/contracts/summary")
async def get_contract_summary(
    year: int = None,
    month: int = None,
    skip_cache: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get summary statistics for contracts.
    If year/month provided, filter by sign_date.
    Results are cached for 5 minutes.
    """
    if not year:
        year = datetime.now().year
    
    # Try to get from cache first
    if not skip_cache:
        cached_data = await get_cached_report("contracts_summary", year, month)
        if cached_data:
            logger.debug(f"[CACHE] Contract summary served from cache: {year}/{month}")
            return cached_data

    # Base filters
    up_filters = [cast(extract('year', ContractUpstream.sign_date), Integer) == year]
    down_filters = [cast(extract('year', ContractDownstream.sign_date), Integer) == year]
    mgmt_filters = [cast(extract('year', ContractManagement.sign_date), Integer) == year]
    
    if month:
        up_filters.append(cast(extract('month', ContractUpstream.sign_date), Integer) == month)
        down_filters.append(cast(extract('month', ContractDownstream.sign_date), Integer) == month)
        mgmt_filters.append(cast(extract('month', ContractManagement.sign_date), Integer) == month)

    # Upstream by Category
    stmt_up_cat = select(
        ContractUpstream.category,
        func.count(ContractUpstream.id),
        func.sum(ContractUpstream.contract_amount)
    ).where(*up_filters).group_by(ContractUpstream.category)
    
    res_up_cat = await db.execute(stmt_up_cat)
    upstream_by_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_up_cat.all()]

    # Upstream by Company Category
    stmt_up_comp_cat = select(
        ContractUpstream.company_category,
        func.count(ContractUpstream.id),
        func.sum(ContractUpstream.contract_amount)
    ).where(*up_filters).group_by(ContractUpstream.company_category)
    
    res_up_comp_cat = await db.execute(stmt_up_comp_cat)
    upstream_by_company_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_up_comp_cat.all()]

    # Downstream by Category
    stmt_down_cat = select(
        ContractDownstream.category,
        func.count(ContractDownstream.id),
        func.sum(ContractDownstream.contract_amount)
    ).where(*down_filters).group_by(ContractDownstream.category)
    
    res_down_cat = await db.execute(stmt_down_cat)
    downstream_by_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_down_cat.all()]
    
    # Management by Category
    stmt_mgmt_cat = select(
        ContractManagement.category,
        func.count(ContractManagement.id),
        func.sum(ContractManagement.contract_amount)
    ).where(*mgmt_filters).group_by(ContractManagement.category)
        
    res_mgmt_cat = await db.execute(stmt_mgmt_cat)
    management_by_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_mgmt_cat.all()]
    
    result = {
        "upstream_by_category": upstream_by_category,
        "upstream_by_company_category": upstream_by_company_category,
        "downstream_by_category": downstream_by_category,
        "management_by_category": management_by_category
    }
    
    # Cache the result
    await set_cached_report("contracts_summary", year, month, result)
    
    return result


@router.get("/finance/trend")
async def get_finance_trend(
    year: int = None,
    skip_cache: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get monthly income vs expense trend for a specific year.
    Results are cached for 10 minutes.
    """
    if not year:
        year = datetime.now().year
    
    # Try to get from cache first
    if not skip_cache:
        cached_data = await get_cached_report("finance_trend", year)
        if cached_data:
            logger.debug(f"[CACHE] Finance trend served from cache: {year}")
            return cached_data
        
    # Initialize 12 months data
    months = list(range(1, 13))
    income_data = [0] * 12
    expense_down = [0] * 12
    expense_mgmt = [0] * 12
    expense_nc = [0] * 12
    expense_zhl = [0] * 12
    
    # Income (Upstream Receipts)
    stmt_income = select(
        extract('month', FinanceUpstreamReceipt.receipt_date).label('month'),
        func.sum(FinanceUpstreamReceipt.amount)
    ).where(
        extract('year', FinanceUpstreamReceipt.receipt_date) == year
    ).group_by('month')
    
    res_income = await db.execute(stmt_income)
    for r in res_income.all():
        month_idx = int(r[0]) - 1
        if 0 <= month_idx < 12:
            income_data[month_idx] = float(r[1] or 0)
            
    # Downstream Payments
    stmt_exp_down = select(
        extract('month', FinanceDownstreamPayment.payment_date).label('month'),
        func.sum(FinanceDownstreamPayment.amount)
    ).where(
        extract('year', FinanceDownstreamPayment.payment_date) == year
    ).group_by('month')
    res_exp_down = await db.execute(stmt_exp_down)
    for r in res_exp_down.all():
        month_idx = int(r[0]) - 1
        if 0 <= month_idx < 12:
            expense_down[month_idx] = float(r[1] or 0)
            
    # Management Payments
    stmt_exp_mgmt = select(
        extract('month', FinanceManagementPayment.payment_date).label('month'),
        func.sum(FinanceManagementPayment.amount)
    ).where(
        extract('year', FinanceManagementPayment.payment_date) == year
    ).group_by('month')
    res_exp_mgmt = await db.execute(stmt_exp_mgmt)
    for r in res_exp_mgmt.all():
        month_idx = int(r[0]) - 1
        if 0 <= month_idx < 12:
            expense_mgmt[month_idx] = float(r[1] or 0)
            
    # Non-Contract Expenses
    stmt_exp_nc = select(
        extract('month', ExpenseNonContract.expense_date).label('month'),
        func.sum(ExpenseNonContract.amount)
    ).where(
        extract('year', ExpenseNonContract.expense_date) == year
    ).group_by('month')
    res_exp_nc = await db.execute(stmt_exp_nc)
    for r in res_exp_nc.all():
        month_idx = int(r[0]) - 1
        if 0 <= month_idx < 12:
            expense_nc[month_idx] = float(r[1] or 0)

    # Zero Hour Labor
    from app.models.zero_hour_labor import ZeroHourLabor
    stmt_exp_zhl = select(
        extract('month', ZeroHourLabor.labor_date).label('month'),
        func.sum(ZeroHourLabor.total_amount)
    ).where(
        extract('year', ZeroHourLabor.labor_date) == year
    ).group_by('month')
    res_exp_zhl = await db.execute(stmt_exp_zhl)
    for r in res_exp_zhl.all():
        month_idx = int(r[0]) - 1
        if 0 <= month_idx < 12:
            expense_zhl[month_idx] = float(r[1] or 0)

    # Calculate Total Expense
    expense_data = [sum(x) for x in zip(expense_down, expense_mgmt, expense_nc, expense_zhl)]

    result = {
        "year": year,
        "months": [f"{m}月" for m in months],
        "income": income_data,
        "expense": expense_data,
        "expense_breakdown": {
            "downstream": expense_down,
            "management": expense_mgmt,
            "non_contract": expense_nc,
            "zero_hour_labor": expense_zhl
        }
    }
    
    # Cache the result
    await set_cached_report("finance_trend", year, None, result)
    
    return result


@router.get("/expenses/breakdown")
async def get_expense_breakdown(
    year: int = None,
    month: int = None,
    skip_cache: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get breakdown of expenses (Contract vs Non-Contract, and Categories).
    Results are cached for 5 minutes.
    """
    if not year:
        year = datetime.now().year
    
    # Try cache first
    if not skip_cache:
        cached_data = await get_cached_report("expense_breakdown", year, month)
        if cached_data:
            logger.debug(f"[CACHE] Expense breakdown served from cache: {year}/{month}")
            return cached_data
        
    # Filters
    nc_filters = [extract('year', ExpenseNonContract.expense_date) == year]
    down_filters = [extract('year', FinanceDownstreamPayment.payment_date) == year]
    mgmt_filters = [extract('year', FinanceManagementPayment.payment_date) == year]
    
    if month:
        nc_filters.append(extract('month', ExpenseNonContract.expense_date) == month)
        down_filters.append(extract('month', FinanceDownstreamPayment.payment_date) == month)
        mgmt_filters.append(extract('month', FinanceManagementPayment.payment_date) == month)

    # Non-Contract Expense by Type
    stmt_nc_cat = select(
        ExpenseNonContract.expense_type,
        func.count(ExpenseNonContract.id),
        func.sum(ExpenseNonContract.amount)
    ).where(*nc_filters).group_by(ExpenseNonContract.expense_type)
    
    res_nc_cat = await db.execute(stmt_nc_cat)
    
    # Map for translation
    expense_type_map = {
        'MANAGEMENT': '管理费', 'TRAINING': '培训费', 'CATERING': '餐饮费',
        'TRANSPORT': '交通费', 'CONSULTING': '咨询费', 'BUSINESS': '业务费',
        'LEASING': '租赁费', 'QUALIFICATION': '资质费', 'VEHICLE': '车辆使用费',
        '工资': '工资', '奖金': '奖金', '培训费': '培训费', '资质费': '资质费',
        '办公费': '办公费', '餐饮费': '餐饮费', '房屋租赁': '房屋租赁',
        '交通费': '交通费', '车辆使用费': '车辆使用费', '其他租赁': '其他租赁',
        '水电费': '水电费', '业务费': '业务费', '住宿费': '住宿费',
        '通讯费': '通讯费', '投标费': '投标费', '中介费': '中介费',
        '零星采购': '零星采购', '其他费用': '其他费用'
    }

    nc_breakdown = []
    for r in res_nc_cat.all():
        raw_type = r[0] or "未分类"
        name = expense_type_map.get(raw_type, raw_type)
        nc_breakdown.append({"name": name, "count": r[1], "value": float(r[2] or 0)})
    
    # Zero Hour Labor
    from app.models.zero_hour_labor import ZeroHourLabor
    zhl_filters = [extract('year', ZeroHourLabor.labor_date) == year]
    if month:
        zhl_filters.append(extract('month', ZeroHourLabor.labor_date) == month)
    
    stmt_zhl_total = select(func.sum(ZeroHourLabor.total_amount)).where(*zhl_filters)
    res_zhl = await db.execute(stmt_zhl_total)
    total_zhl = float(res_zhl.scalar() or 0)
    
    stmt_zhl_count = select(func.count(ZeroHourLabor.id)).where(*zhl_filters)
    res_zhl_count = await db.execute(stmt_zhl_count)
    count_zhl = res_zhl_count.scalar() or 0
    
    if total_zhl > 0 or count_zhl > 0:
        nc_breakdown.append({"name": "零星用工", "count": count_zhl, "value": total_zhl})
    
    nc_breakdown.sort(key=lambda x: x['value'], reverse=True)
    
    # Totals
    res_down = await db.execute(select(func.sum(FinanceDownstreamPayment.amount)).where(*down_filters))
    total_down = float(res_down.scalar() or 0)
    
    res_mgmt = await db.execute(select(func.sum(FinanceManagementPayment.amount)).where(*mgmt_filters))
    total_mgmt = float(res_mgmt.scalar() or 0)
    
    res_nc = await db.execute(select(func.sum(ExpenseNonContract.amount)).where(*nc_filters))
    total_nc = float(res_nc.scalar() or 0)
    
    overall_breakdown = [
        {"name": "下游合同支出", "value": total_down},
        {"name": "管理合同支出", "value": total_mgmt},
        {"name": "无合同费用", "value": total_nc},
        {"name": "零星用工", "value": total_zhl},
    ]
    
    result = {
        "year": year,
        "non_contract_breakdown": nc_breakdown,
        "overall_breakdown": overall_breakdown,
        "zero_hour_labor": {"count": count_zhl, "total": total_zhl}
    }
    
    await set_cached_report("expense_breakdown", year, month, result)
    
    return result


@router.get("/finance/receivables-payables")
async def get_ar_ap_stats(
    year: int = None,
    month: int = None,
    skip_cache: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AR/AP stats.
    Results are cached for 5 minutes.
    """
    if not year:
        year = datetime.now().year
    
    # Try cache first
    if not skip_cache:
        cached_data = await get_cached_report("ar_ap_stats", year, month)
        if cached_data:
            logger.debug(f"[CACHE] AR/AP stats served from cache: {year}/{month}")
            return cached_data
    
    # Filters
    ar_filters = [cast(extract('year', FinanceUpstreamReceivable.expected_date), Integer) == year]
    rec_filters = [cast(extract('year', FinanceUpstreamReceipt.receipt_date), Integer) == year]
    
    ap_down_filters = [cast(extract('year', FinanceDownstreamPayable.expected_date), Integer) == year]
    paid_down_filters = [cast(extract('year', FinanceDownstreamPayment.payment_date), Integer) == year]
    
    ap_mgmt_filters = [cast(extract('year', FinanceManagementPayable.expected_date), Integer) == year]
    paid_mgmt_filters = [cast(extract('year', FinanceManagementPayment.payment_date), Integer) == year]
    
    if month:
        ar_filters.append(cast(extract('month', FinanceUpstreamReceivable.expected_date), Integer) == month)
        rec_filters.append(cast(extract('month', FinanceUpstreamReceipt.receipt_date), Integer) == month)
        ap_down_filters.append(cast(extract('month', FinanceDownstreamPayable.expected_date), Integer) == month)
        paid_down_filters.append(cast(extract('month', FinanceDownstreamPayment.payment_date), Integer) == month)
        ap_mgmt_filters.append(cast(extract('month', FinanceManagementPayable.expected_date), Integer) == month)
        paid_mgmt_filters.append(cast(extract('month', FinanceManagementPayment.payment_date), Integer) == month)

    # AR
    res_ar_total = await db.execute(select(func.sum(FinanceUpstreamReceivable.amount)).where(*ar_filters))
    total_ar_plan = res_ar_total.scalar() or 0
    
    res_rec = await db.execute(select(func.sum(FinanceUpstreamReceipt.amount)).where(*rec_filters))
    total_received = res_rec.scalar() or 0
    
    period_outstanding_ar = float(total_ar_plan) - float(total_received)
    
    # AP Downstream
    res_ap_down = await db.execute(select(func.sum(FinanceDownstreamPayable.amount)).where(*ap_down_filters))
    total_ap_down_plan = res_ap_down.scalar() or 0
    
    res_paid_down = await db.execute(select(func.sum(FinanceDownstreamPayment.amount)).where(*paid_down_filters))
    total_paid_down = res_paid_down.scalar() or 0
    
    # AP Management
    res_ap_mgmt = await db.execute(select(func.sum(FinanceManagementPayable.amount)).where(*ap_mgmt_filters))
    total_ap_mgmt_plan = res_ap_mgmt.scalar() or 0
    
    res_paid_mgmt = await db.execute(select(func.sum(FinanceManagementPayment.amount)).where(*paid_mgmt_filters))
    total_paid_mgmt = res_paid_mgmt.scalar() or 0
    
    # Non-Contract
    nc_filters = [extract('year', ExpenseNonContract.expense_date) == year]
    if month:
        nc_filters.append(extract('month', ExpenseNonContract.expense_date) == month)
    res_nc_total = await db.execute(select(func.sum(ExpenseNonContract.amount)).where(*nc_filters))
    total_nc = res_nc_total.scalar() or 0
    
    # Zero Hour Labor
    from app.models.zero_hour_labor import ZeroHourLabor
    zhl_filters = [extract('year', ZeroHourLabor.labor_date) == year]
    if month:
        zhl_filters.append(extract('month', ZeroHourLabor.labor_date) == month)
    res_zhl_total = await db.execute(select(func.sum(ZeroHourLabor.total_amount)).where(*zhl_filters))
    total_zhl = res_zhl_total.scalar() or 0
    
    total_ap_plan = float(total_ap_down_plan) + float(total_ap_mgmt_plan) + float(total_nc) + float(total_zhl)
    total_paid = float(total_paid_down) + float(total_paid_mgmt) + float(total_nc) + float(total_zhl)

    result = {
        "ar": {
            "total_receivable": float(total_ar_plan),
            "total_received": float(total_received),
            "outstanding": period_outstanding_ar
        },
        "ap": {
            "total_payable": total_ap_plan,
            "total_paid": total_paid,
            "outstanding": total_ap_plan - total_paid,
            "breakdown": {
                "downstream_payable": float(total_ap_down_plan),
                "downstream_paid": float(total_paid_down),
                "management_payable": float(total_ap_mgmt_plan),
                "management_paid": float(total_paid_mgmt),
                "non_contract": float(total_nc),
                "zero_hour_labor": float(total_zhl)
            }
        }
    }
    
    await set_cached_report("ar_ap_stats", year, month, result)
    
    return result


@router.get("/cost/monthly-quarterly")
async def get_monthly_quarterly_cost_report(
    year: int = None,
    month: int = None,
    skip_cache: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    按上游合同公司分类统计月度、季度、半年度、年度成本数据。
    统计口径按业务日期（签约/应收应付/挂账/收付款/结算/费用发生/用工日期）。
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    month = max(1, min(12, int(month)))
    cache_key = "cost_monthly_quarterly_v2"

    if not skip_cache:
        cached_data = await get_cached_report(cache_key, year, month)
        if cached_data:
            logger.debug(f"[CACHE] Cost multi-period report served from cache: {year}/{month}")
            return cached_data

    result = await _build_cost_report_payload(db, year, month)

    await set_cached_report(cache_key, year, month, result)
    return result
