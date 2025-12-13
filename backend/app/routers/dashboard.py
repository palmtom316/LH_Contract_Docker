"""
Dashboard Statistics Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayment
from app.models.contract_management import FinanceManagementPayment
from app.models.expense import ExpenseNonContract
from app.services.auth import get_current_active_user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard statistics:
    1. Cards Data (Total Contracts, Total Received, Total Paid, Expenses)
    2. Bar Chart Data (Monthly Income vs Expense)
    3. Pie Chart Data (Contract Categories)
    """
    current_year = datetime.now().year
    
    # --- 1. Top Cards (Annual Statistics for Current Year) ---
    
    # Annual Upstream Contracts (signed in current year)
    res_up_annual = await db.execute(
        select(
            func.count(ContractUpstream.id),
            func.sum(ContractUpstream.contract_amount)
        ).where(extract('year', ContractUpstream.sign_date) == current_year)
    )
    up_annual = res_up_annual.first()
    annual_upstream_count = up_annual[0] or 0
    annual_upstream_amount = up_annual[1] or 0
    
    # Annual Receipts (received in current year)
    res_receipts_annual = await db.execute(
        select(func.sum(FinanceUpstreamReceipt.amount)).where(
            extract('year', FinanceUpstreamReceipt.receipt_date) == current_year
        )
    )
    annual_receipts_amount = res_receipts_annual.scalar() or 0
    
    # Annual Payments (paid in current year: Downstream + Management + Non-Contract Expenses)
    res_paid_down_annual = await db.execute(
        select(func.sum(FinanceDownstreamPayment.amount)).where(
            extract('year', FinanceDownstreamPayment.payment_date) == current_year
        )
    )
    annual_paid_down = res_paid_down_annual.scalar() or 0
    
    res_paid_mgmt_annual = await db.execute(
        select(func.sum(FinanceManagementPayment.amount)).where(
            extract('year', FinanceManagementPayment.payment_date) == current_year
        )
    )
    annual_paid_mgmt = res_paid_mgmt_annual.scalar() or 0
    
    res_paid_exp_annual = await db.execute(
        select(func.sum(ExpenseNonContract.amount)).where(
            extract('year', ExpenseNonContract.expense_date) == current_year
        )
    )
    annual_paid_exp = res_paid_exp_annual.scalar() or 0
    
    annual_payments_amount = float(annual_paid_down or 0) + float(annual_paid_mgmt or 0) + float(annual_paid_exp or 0)
    
    # Annual Downstream + Management Contracts (signed in current year)
    res_down_annual = await db.execute(
        select(
            func.count(ContractDownstream.id),
            func.sum(ContractDownstream.contract_amount)
        ).where(extract('year', ContractDownstream.sign_date) == current_year)
    )
    down_annual = res_down_annual.first()
    annual_down_count = down_annual[0] or 0
    annual_down_amount = down_annual[1] or 0
    
    # Import ContractManagement model
    from app.models.contract_management import ContractManagement
    
    res_mgmt_annual = await db.execute(
        select(
            func.count(ContractManagement.id),
            func.sum(ContractManagement.contract_amount)
        ).where(extract('year', ContractManagement.sign_date) == current_year)
    )
    mgmt_annual = res_mgmt_annual.first()
    annual_mgmt_count = mgmt_annual[0] or 0
    annual_mgmt_amount = mgmt_annual[1] or 0
    
    annual_down_mgmt_count = annual_down_count + annual_mgmt_count
    annual_down_mgmt_amount = float(annual_down_amount or 0) + float(annual_mgmt_amount or 0)
    
    # --- 2. Charts Data (Simplified for MVP) ---
    
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
    
    # Bar Chart: Monthly Receipt vs Payment (Current Year)
    # This involves complex grouping by month. 
    # For MVP, we will return a mockup structure filled with some real aggregations if possible, 
    # but strictly SQL grouping by month can be verbose in SQLAlchemy async.
    # We'll calculate current month stats at least.
    
    current_month = datetime.now().month
    
    stmt_month_in = select(func.sum(FinanceUpstreamReceipt.amount)).where(
        extract('month', FinanceUpstreamReceipt.receipt_date) == current_month,
        extract('year', FinanceUpstreamReceipt.receipt_date) == current_year
    )
    month_in = (await db.execute(stmt_month_in)).scalar() or 0
    
    # Monthly Expense (Downstream Payments + Management Payments + Non-Contract Expenses)
    stmt_month_out_down = select(func.sum(FinanceDownstreamPayment.amount)).where(
        extract('month', FinanceDownstreamPayment.payment_date) == current_month,
        extract('year', FinanceDownstreamPayment.payment_date) == current_year
    )
    month_out_down = (await db.execute(stmt_month_out_down)).scalar() or 0
    
    # Management contract payments
    stmt_month_out_mgmt = select(func.sum(FinanceManagementPayment.amount)).where(
        extract('month', FinanceManagementPayment.payment_date) == current_month,
        extract('year', FinanceManagementPayment.payment_date) == current_year
    )
    month_out_mgmt = (await db.execute(stmt_month_out_mgmt)).scalar() or 0
    
    stmt_month_out_exp = select(func.sum(ExpenseNonContract.amount)).where(
        extract('month', ExpenseNonContract.expense_date) == current_month,
        extract('year', ExpenseNonContract.expense_date) == current_year
    )
    month_out_exp = (await db.execute(stmt_month_out_exp)).scalar() or 0
    
    month_out = float(month_out_down or 0) + float(month_out_mgmt or 0) + float(month_out_exp or 0)
    
    # Constructing a simple mock-ish historical data for frontend demo
    # In production, this should be a full query group by month
    bar_data = {
        "categories": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
        "income": [0] * 12,
        "expense": [0] * 12
    }
    # Fill current month (index starts at 0)
    bar_data["income"][current_month - 1] = float(month_in)
    bar_data["expense"][current_month - 1] = month_out
    
    
    return {
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
            "pie_company": pie_company_data,
            "bar": bar_data
        }
    }
