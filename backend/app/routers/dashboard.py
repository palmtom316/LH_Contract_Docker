"""
Dashboard Statistics Router
Optimized with caching
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, cast, Integer
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayment
from app.models.contract_management import FinanceManagementPayment, ContractManagement
from app.models.expense import ExpenseNonContract
from app.services.report_cache import get_cached_dashboard_stats, set_cached_dashboard_stats
from app.core.permissions import require_permission, Permission
from app.core.cache import cache_manager
from app.services.auth import get_current_active_user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_DASHBOARD))
):
    """
    Get dashboard statistics with caching (5 minute TTL):
    1. Cards Data (Total Contracts, Total Received, Total Paid, Expenses)
    2. Category summary chart data
    """
    current_year = datetime.now().year
    
    # Cache by year (dashboard is same for all users with permission)
    cached = await get_cached_dashboard_stats(current_year, None)
    if cached:
        return cached

    # --- 1. Top Cards (Annual Statistics for Current Year) ---
    
    # Annual Upstream Contracts (signed in current year)
    res_up_annual = await db.execute(
        select(
            func.count(ContractUpstream.id),
            func.sum(ContractUpstream.contract_amount)
        ).where(cast(extract('year', ContractUpstream.sign_date), Integer) == current_year)
    )
    up_annual = res_up_annual.first()
    annual_upstream_count = up_annual[0] or 0
    annual_upstream_amount = up_annual[1] or 0
    
    # Annual Receipts (received in current year)
    res_receipts_annual = await db.execute(
        select(func.sum(FinanceUpstreamReceipt.amount)).where(
            cast(extract('year', FinanceUpstreamReceipt.receipt_date), Integer) == current_year
        )
    )
    annual_receipts_amount = res_receipts_annual.scalar() or 0
    
    # Annual Payments (paid in current year)
    res_paid_down_annual = await db.execute(
        select(func.sum(FinanceDownstreamPayment.amount)).where(
            cast(extract('year', FinanceDownstreamPayment.payment_date), Integer) == current_year
        )
    )
    annual_paid_down = res_paid_down_annual.scalar() or 0
    
    res_paid_mgmt_annual = await db.execute(
        select(func.sum(FinanceManagementPayment.amount)).where(
            cast(extract('year', FinanceManagementPayment.payment_date), Integer) == current_year
        )
    )
    annual_paid_mgmt = res_paid_mgmt_annual.scalar() or 0
    
    res_paid_exp_annual = await db.execute(
        select(func.sum(ExpenseNonContract.amount)).where(
            cast(extract('year', ExpenseNonContract.expense_date), Integer) == current_year
        )
    )
    annual_paid_exp = res_paid_exp_annual.scalar() or 0
    
    # Annual Zero Hour Labor (labor date in current year)
    from app.models.zero_hour_labor import ZeroHourLabor
    res_paid_zhl_annual = await db.execute(
        select(func.sum(ZeroHourLabor.total_amount)).where(
            cast(extract('year', ZeroHourLabor.labor_date), Integer) == current_year
        )
    )
    annual_paid_zhl = res_paid_zhl_annual.scalar() or 0
    
    # Annual Downstream + Management Contracts (signed in current year)
    res_down_annual = await db.execute(
        select(
            func.count(ContractDownstream.id),
            func.sum(ContractDownstream.contract_amount)
        ).where(cast(extract('year', ContractDownstream.sign_date), Integer) == current_year)
    )
    down_annual = res_down_annual.first()
    annual_down_count = down_annual[0] or 0
    annual_down_amount = down_annual[1] or 0
    
    from app.models.contract_management import ContractManagement
    res_mgmt_annual = await db.execute(
        select(
            func.count(ContractManagement.id),
            func.sum(ContractManagement.contract_amount)
        ).where(cast(extract('year', ContractManagement.sign_date), Integer) == current_year)
    )
    mgmt_annual = res_mgmt_annual.first()
    annual_mgmt_count = mgmt_annual[0] or 0
    annual_mgmt_amount = mgmt_annual[1] or 0
    
    annual_payments_amount = float(annual_paid_down or 0) + float(annual_paid_mgmt or 0) + float(annual_paid_exp or 0) + float(annual_paid_zhl or 0)
    annual_down_mgmt_count = annual_down_count + annual_mgmt_count
    annual_down_mgmt_amount = float(annual_down_amount or 0) + float(annual_mgmt_amount or 0)
    
    # --- 2. Charts Data ---
    
    # Pie Chart 1: Upstream Contract Categories
    # Note: Group by Category
    stmt_cat = select(
        ContractUpstream.category, 
        func.sum(ContractUpstream.contract_amount)
    ).group_by(ContractUpstream.category)
    cat_result = await db.execute(stmt_cat)
    pie_category_data = [{"name": r[0].value if hasattr(r[0], 'value') else str(r[0]), "value": float(r[1] or 0)} for r in cat_result.all()]

    # Pie Chart 2: Upstream Contract Company Categories
    stmt_comp_cat = select(
        ContractUpstream.company_category, 
        func.sum(ContractUpstream.contract_amount)
    ).group_by(ContractUpstream.company_category)
    comp_cat_result = await db.execute(stmt_comp_cat)
    pie_company_data = [{"name": r[0] or "未分类", "value": float(r[1] or 0)} for r in comp_cat_result.all()]
    
    result = {
        "cards": {
            "annual_upstream_count": annual_upstream_count,
            "annual_upstream_amount": float(annual_upstream_amount),
            "annual_receipts_amount": float(annual_receipts_amount),
            "annual_payments_amount": annual_payments_amount,
            "annual_down_mgmt_count": annual_down_mgmt_count,
            "annual_down_mgmt_amount": annual_down_mgmt_amount
        },
        "charts": {
            "pie_category": pie_category_data,
            "pie_company": pie_company_data
        }
    }

    await set_cached_dashboard_stats(current_year, None, result)
    return result


@router.get("/stats/period")
async def get_period_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_DASHBOARD))
):
    """
    获取近一月和近一季度的经营统计数据
    """
    from datetime import timedelta
    from app.models.zero_hour_labor import ZeroHourLabor
    
    today = date.today()
    one_month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    
    async def get_period_data(start_date: date, end_date: date):
        """获取指定时间段的统计数据"""
        
        # 上游合同签约数量和金额
        res_upstream = await db.execute(
            select(
                func.count(ContractUpstream.id),
                func.coalesce(func.sum(ContractUpstream.contract_amount), 0)
            ).where(
                ContractUpstream.sign_date >= start_date,
                ContractUpstream.sign_date <= end_date
            )
        )
        upstream = res_upstream.first()
        upstream_count = upstream[0] or 0
        upstream_amount = float(upstream[1] or 0)
        
        # 上游合同回款金额
        res_receipts = await db.execute(
            select(func.coalesce(func.sum(FinanceUpstreamReceipt.amount), 0)).where(
                FinanceUpstreamReceipt.receipt_date >= start_date,
                FinanceUpstreamReceipt.receipt_date <= end_date
            )
        )
        receipts_amount = float(res_receipts.scalar() or 0)
        
        # 下游合同签约数量和金额
        res_downstream = await db.execute(
            select(
                func.count(ContractDownstream.id),
                func.coalesce(func.sum(ContractDownstream.contract_amount), 0)
            ).where(
                ContractDownstream.sign_date >= start_date,
                ContractDownstream.sign_date <= end_date
            )
        )
        downstream = res_downstream.first()
        downstream_count = downstream[0] or 0
        downstream_amount = float(downstream[1] or 0)
        
        # 管理合同签约数量和金额
        res_management = await db.execute(
            select(
                func.count(ContractManagement.id),
                func.coalesce(func.sum(ContractManagement.contract_amount), 0)
            ).where(
                ContractManagement.sign_date >= start_date,
                ContractManagement.sign_date <= end_date
            )
        )
        management = res_management.first()
        management_count = management[0] or 0
        management_amount = float(management[1] or 0)
        
        # 下游及管理合同付款金额
        res_downstream_payment = await db.execute(
            select(func.coalesce(func.sum(FinanceDownstreamPayment.amount), 0)).where(
                FinanceDownstreamPayment.payment_date >= start_date,
                FinanceDownstreamPayment.payment_date <= end_date
            )
        )
        downstream_payment = float(res_downstream_payment.scalar() or 0)
        
        res_management_payment = await db.execute(
            select(func.coalesce(func.sum(FinanceManagementPayment.amount), 0)).where(
                FinanceManagementPayment.payment_date >= start_date,
                FinanceManagementPayment.payment_date <= end_date
            )
        )
        management_payment = float(res_management_payment.scalar() or 0)
        
        # 无合同费用金额
        res_expense = await db.execute(
            select(func.coalesce(func.sum(ExpenseNonContract.amount), 0)).where(
                ExpenseNonContract.expense_date >= start_date,
                ExpenseNonContract.expense_date <= end_date
            )
        )
        expense_amount = float(res_expense.scalar() or 0)
        
        # 零星用工总金额
        res_labor = await db.execute(
            select(func.coalesce(func.sum(ZeroHourLabor.total_amount), 0)).where(
                ZeroHourLabor.labor_date >= start_date,
                ZeroHourLabor.labor_date <= end_date
            )
        )
        labor_amount = float(res_labor.scalar() or 0)
        
        return {
            "upstream_count": upstream_count,
            "upstream_amount": upstream_amount,
            "upstream_receipts": receipts_amount,
            "downstream_mgmt_count": downstream_count + management_count,
            "downstream_mgmt_amount": downstream_amount + management_amount,
            "downstream_mgmt_payment": downstream_payment + management_payment,
            "non_contract_expense": expense_amount,
            "zero_hour_labor": labor_amount
        }
    
    # 获取近一月数据
    monthly_data = await get_period_data(one_month_ago, today)
    
    # 获取近一季度数据
    quarterly_data = await get_period_data(three_months_ago, today)
    
    return {
        "monthly": monthly_data,
        "quarterly": quarterly_data
    }


@router.get("/stats/trend/period")
@cache_manager.cached(ttl=300, key_prefix="dashboard_period_trend")
async def get_period_trend(
    period: str = "monthly",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get trend data (Income vs Expense) for a specific period (monthly=30days, quarterly=90days).
    Returns daily aggregation.
    """
    from datetime import timedelta
    
    today = date.today()
    if period == "quarterly":
        start_date = today - timedelta(days=90)
    else: # default monthly
        start_date = today - timedelta(days=30)
        
    end_date = today

    # Prepare complete date range list to ensure continuity
    date_range = []
    curr = start_date
    while curr <= end_date:
        date_range.append(curr)
        curr += timedelta(days=1)
    
    # 1. Income: Upstream Receipts
    stmt_income = select(
        FinanceUpstreamReceipt.receipt_date,
        func.sum(FinanceUpstreamReceipt.amount)
    ).where(
        FinanceUpstreamReceipt.receipt_date >= start_date,
        FinanceUpstreamReceipt.receipt_date <= end_date
    ).group_by(FinanceUpstreamReceipt.receipt_date)
    
    income_res = await db.execute(stmt_income)
    income_map = {row[0]: float(row[1] or 0) for row in income_res.all()}
    
    # Format Response
    dates = []
    incomes = []
    # Breakdown arrays
    downstream_list = []
    management_list = []
    non_contract_list = []
    labor_list = []
    
    # Maps for individual components - reusing the logic to populate them
    downstream_map = {}
    management_map = {}
    non_contract_map = {}
    labor_map = {}
    
    async def fill_map(stmt, target_map):
        res = await db.execute(stmt)
        for row in res.all():
            d, amt = row[0], float(row[1] or 0)
            target_map[d] = target_map.get(d, 0) + amt

    # Downstream Payment
    await fill_map(select(
        FinanceDownstreamPayment.payment_date,
        func.sum(FinanceDownstreamPayment.amount)
    ).where(
        FinanceDownstreamPayment.payment_date >= start_date,
        FinanceDownstreamPayment.payment_date <= end_date
    ).group_by(FinanceDownstreamPayment.payment_date), downstream_map)
    
    # Management Payment
    await fill_map(select(
        FinanceManagementPayment.payment_date,
        func.sum(FinanceManagementPayment.amount)
    ).where(
        FinanceManagementPayment.payment_date >= start_date,
        FinanceManagementPayment.payment_date <= end_date
    ).group_by(FinanceManagementPayment.payment_date), management_map)
    
    # Non-Contract Expense
    await fill_map(select(
        ExpenseNonContract.expense_date,
        func.sum(ExpenseNonContract.amount)
    ).where(
        ExpenseNonContract.expense_date >= start_date,
        ExpenseNonContract.expense_date <= end_date
    ).group_by(ExpenseNonContract.expense_date), non_contract_map)
    
    # Zero Hour Labor
    from app.models.zero_hour_labor import ZeroHourLabor
    await fill_map(select(
        ZeroHourLabor.labor_date,
        func.sum(ZeroHourLabor.total_amount)
    ).where(
        ZeroHourLabor.labor_date >= start_date,
        ZeroHourLabor.labor_date <= end_date
    ).group_by(ZeroHourLabor.labor_date), labor_map)
    
    for d in date_range:
        dates.append(d.strftime("%Y-%m-%d"))
        incomes.append(income_map.get(d, 0))
        
        # Populate breakdown lists
        downstream_list.append(downstream_map.get(d, 0))
        management_list.append(management_map.get(d, 0))
        non_contract_list.append(non_contract_map.get(d, 0))
        labor_list.append(labor_map.get(d, 0))
        
    return {
        "dates": dates,
        "income": incomes,
        "expense_breakdown": {
            "downstream": downstream_list,
            "management": management_list,
            "non_contract": non_contract_list,
            "labor": labor_list
        }
    }
