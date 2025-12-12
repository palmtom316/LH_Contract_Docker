"""
Report Statistics Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, case
from datetime import datetime, date
from typing import List, Dict, Any

from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt, FinanceUpstreamReceivable, FinanceUpstreamInvoice
from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayment, FinanceDownstreamPayable
from app.models.contract_management import ContractManagement, FinanceManagementPayment, FinanceManagementPayable
from app.models.expense import ExpenseNonContract
from app.services.auth import get_current_active_user

router = APIRouter()

@router.get("/contracts/summary")
async def get_contract_summary(
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get summary statistics for contracts
    If year/month provided, filter by sign_date
    """
    if not year:
        year = datetime.now().year

    # Base filters
    up_filters = [extract('year', ContractUpstream.sign_date) == year]
    down_filters = [extract('year', ContractDownstream.sign_date) == year]
    
    if month:
        up_filters.append(extract('month', ContractUpstream.sign_date) == month)
        down_filters.append(extract('month', ContractDownstream.sign_date) == month)

    # 1a. Upstream Contracts Count & Amount by Category
    stmt_up_cat = select(
        ContractUpstream.category,
        func.count(ContractUpstream.id),
        func.sum(ContractUpstream.contract_amount)
    ).where(*up_filters).group_by(ContractUpstream.category)
    
    res_up_cat = await db.execute(stmt_up_cat)
    upstream_by_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_up_cat.all()]

    # 1b. Upstream Contracts Count & Amount by Company Category
    stmt_up_comp_cat = select(
        ContractUpstream.company_category,
        func.count(ContractUpstream.id),
        func.sum(ContractUpstream.contract_amount)
    ).where(*up_filters).group_by(ContractUpstream.company_category)
    
    res_up_comp_cat = await db.execute(stmt_up_comp_cat)
    upstream_by_company_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_up_comp_cat.all()]

    # 2. Downstream Contracts Count & Amount by Type needed? (Maybe by Category too)
    stmt_down_cat = select(
        ContractDownstream.category,
        func.count(ContractDownstream.id),
        func.sum(ContractDownstream.contract_amount)
    ).where(*down_filters).group_by(ContractDownstream.category)
    
    res_down_cat = await db.execute(stmt_down_cat)
    downstream_by_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_down_cat.all()]
    
    # 3. Management Contracts Count & Amount by Category
    stmt_mgmt_cat = select(
        ContractManagement.category,
        func.count(ContractManagement.id),
        func.sum(ContractManagement.contract_amount)
    ).where(
        extract('year', ContractManagement.sign_date) == year
    ).group_by(ContractManagement.category)
    
    if month:
        stmt_mgmt_cat = stmt_mgmt_cat.where(extract('month', ContractManagement.sign_date) == month)
        
    res_mgmt_cat = await db.execute(stmt_mgmt_cat)
    management_by_category = [{"name": r[0] or "未分类", "count": r[1], "amount": float(r[2] or 0)} for r in res_mgmt_cat.all()]
    
    return {
        "upstream_by_category": upstream_by_category,
        "upstream_by_company_category": upstream_by_company_category,
        "downstream_by_category": downstream_by_category,
        "management_by_category": management_by_category
    }

@router.get("/finance/trend")
async def get_finance_trend(
    year: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get monthly income vs expense trend for a specific year
    """
    if not year:
        year = datetime.now().year
        
    # Initialize 12 months data
    months = list(range(1, 13))
    income_data = [0] * 12
    expense_data = [0] * 12 # Keep for backward compatibility or total
    expense_down = [0] * 12
    expense_mgmt = [0] * 12
    expense_nc = [0] * 12
    
    # 1. Income (Upstream Receipts)
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
            
    # 2. Expense (Downstream Payments + Mgmt Payments + Non-Contract Expenses)
    
    # Downstream
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
            
    # Management
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

    # Calculate Total Expense (sum of components)
    expense_data = [sum(x) for x in zip(expense_down, expense_mgmt, expense_nc)]

    return {
        "year": year,
        "months": [f"{m}月" for m in months],
        "income": income_data,
        "expense": expense_data,
        "expense_breakdown": {
            "downstream": expense_down,
            "management": expense_mgmt,
            "non_contract": expense_nc
        }
    }

@router.get("/expenses/breakdown")
async def get_expense_breakdown(
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get breakdown of expenses (Contract vs Non-Contract, and Categories)
    """
    if not year:
        year = datetime.now().year
        
    # Filters
    nc_filters = [extract('year', ExpenseNonContract.expense_date) == year]
    down_filters = [extract('year', FinanceDownstreamPayment.payment_date) == year]
    mgmt_filters = [extract('year', FinanceManagementPayment.payment_date) == year]
    
    if month:
        nc_filters.append(extract('month', ExpenseNonContract.expense_date) == month)
        down_filters.append(extract('month', FinanceDownstreamPayment.payment_date) == month)
        mgmt_filters.append(extract('month', FinanceManagementPayment.payment_date) == month)

    # 1. Non-Contract Expense by Category
    stmt_nc_cat = select(
        ExpenseNonContract.category,
        func.count(ExpenseNonContract.id),
        func.sum(ExpenseNonContract.amount)
    ).where(*nc_filters).group_by(ExpenseNonContract.category)
    
    res_nc_cat = await db.execute(stmt_nc_cat)
    # value = amount for charts
    nc_breakdown = [{"name": r[0] or "未分类", "count": r[1], "value": float(r[2] or 0)} for r in res_nc_cat.all()]
    
    # 2. Downstream Payments Total
    stmt_down_total = select(func.sum(FinanceDownstreamPayment.amount)).where(*down_filters)
    res_down = await db.execute(stmt_down_total)
    total_down = float(res_down.scalar() or 0)
    
    # 3. Management Payments Total
    stmt_mgmt_total = select(func.sum(FinanceManagementPayment.amount)).where(*mgmt_filters)
    res_mgmt = await db.execute(stmt_mgmt_total)
    total_mgmt = float(res_mgmt.scalar() or 0)
    
    # 4. Total Non-Contract
    stmt_nc_total = select(func.sum(ExpenseNonContract.amount)).where(*nc_filters)
    res_nc = await db.execute(stmt_nc_total)
    total_nc = float(res_nc.scalar() or 0)
    
    overall_breakdown = [
        {"name": "下游合同支出", "value": total_down},
        {"name": "管理合同支出", "value": total_mgmt},
        {"name": "无合同费用", "value": total_nc},
    ]
    
    return {
        "year": year,
        "non_contract_breakdown": nc_breakdown,
        "overall_breakdown": overall_breakdown
    }

@router.get("/finance/receivables-payables")
async def get_ar_ap_stats(
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AR/AP stats.
    NOTE: AR/AP Outstanding is typically a snapshot (all time). 
    However, "Received" and "Paid" should reflect the selected period.
    "Receivable/Payable" in this context will represent 'New AR/AP generated in period'.
    """
    if not year:
        year = datetime.now().year
    
    # Define filters for "Creation" (Receivable/Payable dates) and "Flow" (Receipt/Payment dates)
    # Usually: Receivable.expected_date or created_at? Let's use created_at (registration date) for AR generation stats
    # And Receipt.receipt_date for money flow.
    
    # Actually, UpstreamReceivable doesn't have a date field other than created_at or 'expected_collection_date'.
    # Let's use 'expected_collection_date' for AR planning if available, else created_at.
    # Checking model: FinanceUpstreamReceivable has `expected_date`.
    # FinanceDownstreamPayable has `expected_date`.
    
    ar_filters = [extract('year', FinanceUpstreamReceivable.expected_date) == year]
    rec_filters = [extract('year', FinanceUpstreamReceipt.receipt_date) == year]
    
    ap_down_filters = [extract('year', FinanceDownstreamPayable.expected_date) == year]
    paid_down_filters = [extract('year', FinanceDownstreamPayment.payment_date) == year]
    
    ap_mgmt_filters = [extract('year', FinanceManagementPayable.expected_date) == year]
    paid_mgmt_filters = [extract('year', FinanceManagementPayment.payment_date) == year]
    
    if month:
        ar_filters.append(extract('month', FinanceUpstreamReceivable.expected_date) == month)
        rec_filters.append(extract('month', FinanceUpstreamReceipt.receipt_date) == month)
        ap_down_filters.append(extract('month', FinanceDownstreamPayable.expected_date) == month)
        paid_down_filters.append(extract('month', FinanceDownstreamPayment.payment_date) == month)
        ap_mgmt_filters.append(extract('month', FinanceManagementPayable.expected_date) == month)
        paid_mgmt_filters.append(extract('month', FinanceManagementPayment.payment_date) == month)

    # AR
    # Total Receivables (Planned in period)
    res_ar_total = await db.execute(select(func.sum(FinanceUpstreamReceivable.amount)).where(*ar_filters))
    total_ar_plan = res_ar_total.scalar() or 0
    
    # Total Received (Actual in period)
    res_rec = await db.execute(select(func.sum(FinanceUpstreamReceipt.amount)).where(*rec_filters))
    total_received = res_rec.scalar() or 0
    
    # Outstanding (This period's balance impact)
    # Note: This is not "Total Portfolio Outstanding", but "Net Flow for Period"
    period_outstanding_ar = float(total_ar_plan) - float(total_received)
    
    # AP
    # Downstream
    res_ap_down = await db.execute(select(func.sum(FinanceDownstreamPayable.amount)).where(*ap_down_filters))
    total_ap_down_plan = res_ap_down.scalar() or 0
    
    res_paid_down = await db.execute(select(func.sum(FinanceDownstreamPayment.amount)).where(*paid_down_filters))
    total_paid_down = res_paid_down.scalar() or 0
    
    # Management
    res_ap_mgmt = await db.execute(select(func.sum(FinanceManagementPayable.amount)).where(*ap_mgmt_filters))
    total_ap_mgmt_plan = res_ap_mgmt.scalar() or 0
    
    res_paid_mgmt = await db.execute(select(func.sum(FinanceManagementPayment.amount)).where(*paid_mgmt_filters))
    total_paid_mgmt = res_paid_mgmt.scalar() or 0
    
    # Non-Contract Expenses (Payable = Paid for this context)
    nc_filters = [extract('year', ExpenseNonContract.expense_date) == year]
    if month:
        nc_filters.append(extract('month', ExpenseNonContract.expense_date) == month)

    res_nc_total = await db.execute(select(func.sum(ExpenseNonContract.amount)).where(*nc_filters))
    total_nc = res_nc_total.scalar() or 0
    
    total_ap_plan = float(total_ap_down_plan) + float(total_ap_mgmt_plan) + float(total_nc)
    total_paid = float(total_paid_down) + float(total_paid_mgmt) + float(total_nc)

    return {
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
                "management_paid": float(total_paid_mgmt)
            }
        }
    }
