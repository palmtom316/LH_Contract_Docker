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
    
    # --- 1. Top Cards ---
    
    # Total Upstream Contract Amount
    res_up_total = await db.execute(select(func.sum(ContractUpstream.contract_amount)))
    total_contract_amount = res_up_total.scalar() or 0
    
    # Total Actual Received (Income)
    res_received = await db.execute(select(func.sum(FinanceUpstreamReceipt.amount)))
    total_received = res_received.scalar() or 0
    
    # Total Actual Paid (Downstream + Expenses) - Simplified
    res_paid_down = await db.execute(select(func.sum(FinanceDownstreamPayment.amount)))
    total_paid_down = res_paid_down.scalar() or 0
    
    res_paid_exp = await db.execute(select(func.sum(ExpenseNonContract.amount)))
    total_paid_exp = res_paid_exp.scalar() or 0
    
    total_paid = total_paid_down + total_paid_exp
    
    # Downstream Contract Amount (Pending mostly)
    res_down_total = await db.execute(select(func.sum(ContractDownstream.contract_amount)))
    total_down_contract_amount = res_down_total.scalar() or 0
    
    # --- 2. Charts Data (Simplified for MVP) ---
    
    # Pie Chart: Upstream Contract Categories
    # Note: Group by Category
    stmt_cat = select(
        ContractUpstream.category, 
        func.count(ContractUpstream.id)
    ).group_by(ContractUpstream.category)
    cat_result = await db.execute(stmt_cat)
    pie_data = [{"name": r[0].value if hasattr(r[0], 'value') else str(r[0]), "value": r[1]} for r in cat_result.all()]
    
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
    
    # Constructing a simple mock-ish historical data for frontend demo
    # In production, this should be a full query group by month
    bar_data = {
        "categories": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
        "income": [0] * 12,
        "expense": [0] * 12
    }
    # Fill current month (index starts at 0)
    bar_data["income"][current_month - 1] = float(month_in)
    
    return {
        "cards": {
            "total_contract_amount": float(total_contract_amount),
            "total_received": float(total_received),
            "total_paid": float(total_paid),
            "total_down_contract_amount": float(total_down_contract_amount)
        },
        "charts": {
            "pie": pie_data,
            "bar": bar_data
        }
    }
