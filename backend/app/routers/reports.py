"""
Report Statistics Router (Reloaded)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, extract, case, or_, cast, String, Integer
from datetime import datetime, date
from typing import List, Dict, Any

from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt, FinanceUpstreamReceivable, FinanceUpstreamInvoice, ProjectSettlement
from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayment, FinanceDownstreamInvoice, FinanceDownstreamPayable, DownstreamSettlement
from app.models.contract_management import ContractManagement, FinanceManagementPayment, FinanceManagementInvoice, FinanceManagementPayable, ManagementSettlement
from app.models.expense import ExpenseNonContract
from app.services.auth import get_current_active_user
import pandas as pd
import io
from urllib.parse import quote
from fastapi.responses import StreamingResponse
from urllib.parse import quote

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

    # Base filters using CAST to ensure consistent type comparison across DB dialects
    up_filters = [cast(extract('year', ContractUpstream.sign_date), Integer) == year]
    down_filters = [cast(extract('year', ContractDownstream.sign_date), Integer) == year]
    mgmt_filters = [cast(extract('year', ContractManagement.sign_date), Integer) == year]
    
    if month:
        up_filters.append(cast(extract('month', ContractUpstream.sign_date), Integer) == month)
        down_filters.append(cast(extract('month', ContractDownstream.sign_date), Integer) == month)
        mgmt_filters.append(cast(extract('month', ContractManagement.sign_date), Integer) == month)

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
    ).where(*mgmt_filters).group_by(ContractManagement.category)
        
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

    # 1. Non-Contract Expense by Classification (Expense Type)
    stmt_nc_cat = select(
        ExpenseNonContract.expense_type,
        func.count(ExpenseNonContract.id),
        func.sum(ExpenseNonContract.amount)
    ).where(*nc_filters).group_by(ExpenseNonContract.expense_type)
    
    res_nc_cat = await db.execute(stmt_nc_cat)
    
    # Map for translation
    expense_type_map = {
        'MANAGEMENT': '管理费',
        'TRAINING': '培训费',
        'CATERING': '餐饮费',
        'TRANSPORT': '交通费',
        'CONSULTING': '咨询费',
        'BUSINESS': '业务费',
        'LEASING': '租赁费',
        'QUALIFICATION': '资质费',
        'VEHICLE': '车辆使用费',
        # Keep Chinese keys if they exist directly
        '工资': '工资',
        '奖金': '奖金',
        '培训费': '培训费',
        '资质费': '资质费',
        '办公费': '办公费',
        '餐饮费': '餐饮费',
        '房屋租赁': '房屋租赁',
        '交通费': '交通费',
        '车辆使用费': '车辆使用费',
        '其他租赁': '其他租赁',
        '水电费': '水电费',
        '业务费': '业务费',
        '住宿费': '住宿费',
        '通讯费': '通讯费',
        '投标费': '投标费',
        '中介费': '中介费',
        '零星采购': '零星采购',
        '其他费用': '其他费用'
    }

    # value = amount for charts
    nc_breakdown = []
    for r in res_nc_cat.all():
        raw_type = r[0] or "未分类"
        name = expense_type_map.get(raw_type, raw_type)
        nc_breakdown.append({"name": name, "count": r[1], "value": float(r[2] or 0)})
    
    # Sort by value descending to show top expenses first
    nc_breakdown.sort(key=lambda x: x['value'], reverse=True)
    
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


@router.get("/export/comprehensive")
async def export_comprehensive_report(
    start_date: date = None,
    end_date: date = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export comprehensive report to Excel
    """
    # 1. Fetch Upstream Contracts
    stmt = select(ContractUpstream).options(
        selectinload(ContractUpstream.settlements),
        selectinload(ContractUpstream.receipts),
        selectinload(ContractUpstream.receivables),
        selectinload(ContractUpstream.invoices)
    )
    
    if start_date:
        stmt = stmt.where(ContractUpstream.sign_date >= start_date)
    if end_date:
        stmt = stmt.where(ContractUpstream.sign_date <= end_date)
    if status and status != '全部':
        stmt = stmt.where(ContractUpstream.status == status)
    
    stmt = stmt.order_by(ContractUpstream.sign_date.desc())
    
    result = await db.execute(stmt)
    contracts = result.scalars().all()
    
    if not contracts:
        # Return empty excel
        df = pd.DataFrame()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=report.xlsx"}
        )

    upstream_ids = [c.id for c in contracts]
    
    # 2. Aggregations using helper function
    async def get_agg(stmt_select):
        res = await db.execute(stmt_select)
        return {r[0]: float(r[1] or 0) for r in res.all()}

    # Downstream Aggregations
    # Settlement
    stmt_down_set = select(ContractDownstream.upstream_contract_id, func.sum(DownstreamSettlement.settlement_amount))\
        .join(DownstreamSettlement, DownstreamSettlement.contract_id == ContractDownstream.id)\
        .where(ContractDownstream.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractDownstream.upstream_contract_id)
    map_down_set = await get_agg(stmt_down_set)
    
    # Payable (Invoices Received)
    stmt_down_pay = select(ContractDownstream.upstream_contract_id, func.sum(FinanceDownstreamInvoice.amount))\
        .join(FinanceDownstreamInvoice, FinanceDownstreamInvoice.contract_id == ContractDownstream.id)\
        .where(ContractDownstream.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractDownstream.upstream_contract_id)
    map_down_pay = await get_agg(stmt_down_pay)
    
    # Paid
    stmt_down_paid = select(ContractDownstream.upstream_contract_id, func.sum(FinanceDownstreamPayment.amount))\
        .join(FinanceDownstreamPayment, FinanceDownstreamPayment.contract_id == ContractDownstream.id)\
        .where(ContractDownstream.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractDownstream.upstream_contract_id)
    map_down_paid = await get_agg(stmt_down_paid)

    # Management Aggregations
    # Settlement
    stmt_mgmt_set = select(ContractManagement.upstream_contract_id, func.sum(ManagementSettlement.settlement_amount))\
        .join(ManagementSettlement, ManagementSettlement.contract_id == ContractManagement.id)\
        .where(ContractManagement.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractManagement.upstream_contract_id)
    map_mgmt_set = await get_agg(stmt_mgmt_set)
    
    # Payable (Invoices Received)
    stmt_mgmt_pay = select(ContractManagement.upstream_contract_id, func.sum(FinanceManagementInvoice.amount))\
        .join(FinanceManagementInvoice, FinanceManagementInvoice.contract_id == ContractManagement.id)\
        .where(ContractManagement.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractManagement.upstream_contract_id)
    map_mgmt_pay = await get_agg(stmt_mgmt_pay)
    
    # Paid
    stmt_mgmt_paid = select(ContractManagement.upstream_contract_id, func.sum(FinanceManagementPayment.amount))\
        .join(FinanceManagementPayment, FinanceManagementPayment.contract_id == ContractManagement.id)\
        .where(ContractManagement.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractManagement.upstream_contract_id)
    map_mgmt_paid = await get_agg(stmt_mgmt_paid)

    # Expense Aggregation
    stmt_exp = select(ExpenseNonContract.upstream_contract_id, func.sum(ExpenseNonContract.amount))\
        .where(ExpenseNonContract.upstream_contract_id.in_(upstream_ids))\
        .group_by(ExpenseNonContract.upstream_contract_id)
    map_exp = await get_agg(stmt_exp)

    # 3. Assemble Data
    data_list = []
    for c in contracts:
        # Basic
        settlement = c.settlements[0] if c.settlements else None
        
        row = {
            "合同序号": c.serial_number,
            "合同编号": c.contract_code,
            "合同名称": c.contract_name,
            "合同甲方单位": c.party_a_name,
            "合同乙方单位": c.party_b_name,
            "签约时间": c.sign_date,
            "签约金额": float(c.contract_amount or 0),
            "完工时间": settlement.completion_date if settlement else None,
            "结算办结时间": settlement.settlement_date if settlement else None,
            "结算金额": float(settlement.settlement_amount or 0) if settlement else 0,
            
            # Upstream Financials
            "累计应收款": sum([float(r.amount or 0) for r in c.receivables]),
            "累计挂账金额": sum([float(i.amount or 0) for i in c.invoices]),
            "累计付款金额": sum([float(r.amount or 0) for r in c.receipts]), # "付款" as per request, mapped to Receipts
            
            # Associated Downstream
            "关联下游合同结算金额合计": map_down_set.get(c.id, 0),
            "关联下游合同应付款合计": map_down_pay.get(c.id, 0),
            "关联下游合同已付款合计": map_down_paid.get(c.id, 0),
            
            # Associated Management
            "关联管理合同结算金额合计": map_mgmt_set.get(c.id, 0),
            "关联管理合同应付款合计": map_mgmt_pay.get(c.id, 0),
            "关联管理合同已付款合计": map_mgmt_paid.get(c.id, 0),
            
            # Associated Expense
            "关联无合同费用付款合计": map_exp.get(c.id, 0),
        }
        data_list.append(row)
        
    # 4. Generate Excel
    df = pd.DataFrame(data_list)
    
    # Format dates
    date_cols = ["签约时间", "完工时间", "结算办结时间"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
    
    output = io.BytesIO()
    # Auto-adjust column width (simple estimation)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='综合报表')
        worksheet = writer.sheets['综合报表']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    
    filename = f"综合报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/receivables")
async def export_receivables(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Upstream Receivables
    """
    stmt = select(FinanceUpstreamReceivable, ContractUpstream).join(ContractUpstream)
    
    if start_date:
        stmt = stmt.where(FinanceUpstreamReceivable.expected_date >= start_date)
    if end_date:
        stmt = stmt.where(FinanceUpstreamReceivable.expected_date <= end_date)
    
    stmt = stmt.order_by(FinanceUpstreamReceivable.expected_date.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data_list = []
    for idx, (rec, contract) in enumerate(rows, 1):
        data_list.append({
            "序号": idx,
            "上游合同编号": contract.contract_code,
            "上游合同名称": contract.contract_name,
            "应收日期": rec.expected_date,
            "应收金额": float(rec.amount or 0),
            "备注": rec.description or "" # Using description as remarks
        })
        
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='应收款明细')
        worksheet = writer.sheets['应收款明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"上游合同应收款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/payables")
async def export_payables(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Downstream/Management Payables
    """
    # Combine Downstream and Management Payables
    data_list = []
    idx_counter = 1
    
    # 1. Downstream
    stmt_down = select(FinanceDownstreamPayable, ContractDownstream).join(ContractDownstream)
    if start_date:
        stmt_down = stmt_down.where(FinanceDownstreamPayable.expected_date >= start_date)
    if end_date:
        stmt_down = stmt_down.where(FinanceDownstreamPayable.expected_date <= end_date)
    
    res_down = await db.execute(stmt_down)
    for pay, contract in res_down.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "下游合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "应付日期": pay.expected_date,
            "应付金额": float(pay.amount or 0),
            "备注": pay.description or ""
        })
        idx_counter += 1
        
    # 2. Management
    stmt_mgmt = select(FinanceManagementPayable, ContractManagement).join(ContractManagement)
    if start_date:
        stmt_mgmt = stmt_mgmt.where(FinanceManagementPayable.expected_date >= start_date)
    if end_date:
        stmt_mgmt = stmt_mgmt.where(FinanceManagementPayable.expected_date <= end_date)
        
    res_mgmt = await db.execute(stmt_mgmt)
    for pay, contract in res_mgmt.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "管理合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "应付日期": pay.expected_date,
            "应付金额": float(pay.amount or 0),
            "备注": pay.description or ""
        })
        idx_counter += 1
        
    df = pd.DataFrame(data_list)
    # Sort by date
    if not df.empty and '应付日期' in df.columns:
        df['应付日期'] = pd.to_datetime(df['应付日期'])
        df = df.sort_values(by='应付日期', ascending=False)
        df['应付日期'] = df['应付日期'].dt.date
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='应付款明细')
        worksheet = writer.sheets['应付款明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"应付款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/invoices/upstream")
async def export_upstream_invoices(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Upstream Invoices (Guazhang)
    """
    stmt = select(FinanceUpstreamInvoice, ContractUpstream).join(ContractUpstream)
    
    if start_date:
        stmt = stmt.where(FinanceUpstreamInvoice.invoice_date >= start_date)
    if end_date:
        stmt = stmt.where(FinanceUpstreamInvoice.invoice_date <= end_date)
    
    stmt = stmt.order_by(FinanceUpstreamInvoice.invoice_date.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data_list = []
    for idx, (inv, contract) in enumerate(rows, 1):
        data_list.append({
            "序号": idx,
            "上游合同编号": contract.contract_code,
            "上游合同名称": contract.contract_name,
            "挂账日期": inv.invoice_date,
            "挂账金额": float(inv.amount or 0),
            "发票号码": inv.invoice_number or "",
            "备注": inv.description or ""
        })
        
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='挂账明细')
        worksheet = writer.sheets['挂账明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"上游合同挂账报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/invoices/downstream")
async def export_downstream_invoices(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Downstream/Management Invoices (Guazhang)
    """
    data_list = []
    idx_counter = 1
    
    # 1. Downstream
    stmt_down = select(FinanceDownstreamInvoice, ContractDownstream).join(ContractDownstream)
    if start_date:
        stmt_down = stmt_down.where(FinanceDownstreamInvoice.invoice_date >= start_date)
    if end_date:
        stmt_down = stmt_down.where(FinanceDownstreamInvoice.invoice_date <= end_date)
    
    res_down = await db.execute(stmt_down)
    for inv, contract in res_down.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "下游合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "挂账日期": inv.invoice_date,
            "挂账金额": float(inv.amount or 0),
            "发票号码": inv.invoice_number or "",
            "备注": inv.description or ""
        })
        idx_counter += 1
        
    # 2. Management
    stmt_mgmt = select(FinanceManagementInvoice, ContractManagement).join(ContractManagement)
    if start_date:
        stmt_mgmt = stmt_mgmt.where(FinanceManagementInvoice.invoice_date >= start_date)
    if end_date:
        stmt_mgmt = stmt_mgmt.where(FinanceManagementInvoice.invoice_date <= end_date)
        
    res_mgmt = await db.execute(stmt_mgmt)
    for inv, contract in res_mgmt.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "管理合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "挂账日期": inv.invoice_date,
            "挂账金额": float(inv.amount or 0),
            "发票号码": inv.invoice_number or "",
            "备注": inv.description or ""
        })
        idx_counter += 1
        
    df = pd.DataFrame(data_list)
    # Sort by date
    if not df.empty and '挂账日期' in df.columns:
        df['挂账日期'] = pd.to_datetime(df['挂账日期'])
        df = df.sort_values(by='挂账日期', ascending=False)
        df['挂账日期'] = df['挂账日期'].dt.date
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='挂账明细')
        worksheet = writer.sheets['挂账明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"下游及管理合同挂账报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/receipts/upstream")
async def export_upstream_receipts(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Upstream Receipts (实际收款)
    """
    stmt = select(FinanceUpstreamReceipt, ContractUpstream).join(ContractUpstream)
    
    if start_date:
        stmt = stmt.where(FinanceUpstreamReceipt.receipt_date >= start_date)
    if end_date:
        stmt = stmt.where(FinanceUpstreamReceipt.receipt_date <= end_date)
    
    stmt = stmt.order_by(FinanceUpstreamReceipt.receipt_date.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data_list = []
    for idx, (rec, contract) in enumerate(rows, 1):
        data_list.append({
            "序号": idx,
            "上游合同编号": contract.contract_code,
            "上游合同名称": contract.contract_name,
            "收款日期": rec.receipt_date,
            "收款金额": float(rec.amount or 0),
            "收款方式": rec.payment_method or "",
            "付款方名称": rec.payer_name or "",
            "备注": rec.description or ""
        })
        
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='收款明细')
        worksheet = writer.sheets['收款明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"上游合同收款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/payments/downstream")
async def export_downstream_payments(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Downstream/Management Payments (实际付款)
    """
    data_list = []
    idx_counter = 1
    
    # 1. Downstream
    stmt_down = select(FinanceDownstreamPayment, ContractDownstream).join(ContractDownstream)
    if start_date:
        stmt_down = stmt_down.where(FinanceDownstreamPayment.payment_date >= start_date)
    if end_date:
        stmt_down = stmt_down.where(FinanceDownstreamPayment.payment_date <= end_date)
    
    res_down = await db.execute(stmt_down)
    for pay, contract in res_down.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "下游合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "付款日期": pay.payment_date,
            "付款金额": float(pay.amount or 0),
            "付款方式": pay.payment_method or "",
            "收款方名称": getattr(pay, 'payee_name', '') or "",
            "备注": getattr(pay, 'description', '') or ""
        })
        idx_counter += 1
        
    # 2. Management
    stmt_mgmt = select(FinanceManagementPayment, ContractManagement).join(ContractManagement)
    if start_date:
        stmt_mgmt = stmt_mgmt.where(FinanceManagementPayment.payment_date >= start_date)
    if end_date:
        stmt_mgmt = stmt_mgmt.where(FinanceManagementPayment.payment_date <= end_date)
        
    res_mgmt = await db.execute(stmt_mgmt)
    for pay, contract in res_mgmt.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "管理合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "付款日期": pay.payment_date,
            "付款金额": float(pay.amount or 0),
            "付款方式": pay.payment_method or "",
            "备注": getattr(pay, 'description', '') or ""
        })
        idx_counter += 1
        
    df = pd.DataFrame(data_list)
    # Sort by date
    if not df.empty and '付款日期' in df.columns:
        df['付款日期'] = pd.to_datetime(df['付款日期'])
        df = df.sort_values(by='付款日期', ascending=False)
        df['付款日期'] = df['付款日期'].dt.date
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='付款明细')
        worksheet = writer.sheets['付款明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"下游及管理合同付款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/payments/expenses")
async def export_expense_payments(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Non-Contract Expense Payments (无合同费用)
    """
    stmt = select(ExpenseNonContract).options(selectinload(ExpenseNonContract.upstream_contract))
    
    if start_date:
        stmt = stmt.where(ExpenseNonContract.expense_date >= start_date)
    if end_date:
        stmt = stmt.where(ExpenseNonContract.expense_date <= end_date)
    
    stmt = stmt.order_by(ExpenseNonContract.expense_date.desc())
    
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
    data_list = []
    for idx, exp in enumerate(rows, 1):
        data_list.append({
            "序号": idx,
            "费用归属": exp.attribution or "",
            "费用类别": exp.category or "",
            "费用分类": exp.expense_type or "",
            "关联上游合同": exp.upstream_contract.contract_name if exp.upstream_contract else "",
            "发生日期": exp.expense_date,
            "金额": float(exp.amount or 0),
            "经办人": exp.handler or "",
            "说明": exp.description or ""
        })
        
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='费用明细')
        worksheet = writer.sheets['费用明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"无合同费用付款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/settlements/upstream")
async def export_upstream_settlements(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Upstream Settlements (项目结算)
    """
    stmt = select(ProjectSettlement, ContractUpstream).join(ContractUpstream)
    
    if start_date:
        stmt = stmt.where(ProjectSettlement.settlement_date >= start_date)
    if end_date:
        stmt = stmt.where(ProjectSettlement.settlement_date <= end_date)
    
    stmt = stmt.order_by(ProjectSettlement.settlement_date.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data_list = []
    for idx, (st, contract) in enumerate(rows, 1):
        data_list.append({
            "序号": idx,
            "上游合同编号": contract.contract_code,
            "上游合同名称": contract.contract_name,
            "结算日期": st.settlement_date,
            "结算金额": float(st.settlement_amount or 0),
            "完工日期": st.completion_date,
            "备注": st.description or ""
        })
        
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='结算明细')
        worksheet = writer.sheets['结算明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"上游合同结算报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/settlements/downstream")
async def export_downstream_settlements(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Downstream/Management Settlements (结算记录)
    """
    data_list = []
    idx_counter = 1
    
    # 1. Downstream
    stmt_down = select(DownstreamSettlement, ContractDownstream).join(ContractDownstream)
    if start_date:
        stmt_down = stmt_down.where(DownstreamSettlement.settlement_date >= start_date)
    if end_date:
        stmt_down = stmt_down.where(DownstreamSettlement.settlement_date <= end_date)
    
    res_down = await db.execute(stmt_down)
    for st, contract in res_down.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "下游合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "结算日期": st.settlement_date,
            "结算金额": float(st.settlement_amount or 0),
            "备注": st.description or ""
        })
        idx_counter += 1
        
    # 2. Management
    stmt_mgmt = select(ManagementSettlement, ContractManagement).join(ContractManagement)
    if start_date:
        stmt_mgmt = stmt_mgmt.where(ManagementSettlement.settlement_date >= start_date)
    if end_date:
        stmt_mgmt = stmt_mgmt.where(ManagementSettlement.settlement_date <= end_date)
        
    res_mgmt = await db.execute(stmt_mgmt)
    for st, contract in res_mgmt.all():
        data_list.append({
            "序号": idx_counter,
            "类型": "管理合同",
            "合同编号": contract.contract_code,
            "合同名称": contract.contract_name,
            "结算日期": st.settlement_date,
            "结算金额": float(st.settlement_amount or 0),
            "备注": st.description or ""
        })
        idx_counter += 1
        
    df = pd.DataFrame(data_list)
    # Sort by date
    if not df.empty and '结算日期' in df.columns:
        df['结算日期'] = pd.to_datetime(df['结算日期'])
        df = df.sort_values(by='结算日期', ascending=False)
        df['结算日期'] = df['结算日期'].dt.date
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='结算明细')
        worksheet = writer.sheets['结算明细']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"下游及管理合同结算报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.get("/export/association")
async def export_association_report(
    query: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Upstream-Downstream Association Report
    """
    stmt = select(ContractUpstream).options(
        selectinload(ContractUpstream.settlements),
        selectinload(ContractUpstream.receipts)
    )
    
    if query:
        stmt = stmt.where(
            or_(
                ContractUpstream.contract_code.ilike(f"%{query}%"),
                ContractUpstream.contract_name.ilike(f"%{query}%"),
                cast(ContractUpstream.serial_number, String).ilike(f"%{query}%")
            )
        )
    
    stmt = stmt.order_by(ContractUpstream.contract_code)
    
    result = await db.execute(stmt)
    up_contracts = result.scalars().all()
    
    data_list = []
    
    for up in up_contracts:
        # Upstream Info
        up_settle_amount = 0.0
        up_completion_date = None
        if up.settlements:
             # Take latest
             latest = sorted(up.settlements, key=lambda x: x.settlement_date or date.min, reverse=True)[0]
             up_settle_amount = float(latest.settlement_amount or 0)
             up_completion_date = latest.completion_date
             
        up_received = sum(float(r.amount or 0) for r in up.receipts)
        
        base_info = {
            "上游合同序号": up.serial_number,
            "上游合同名称": up.contract_name,
            "上游签约金额": float(up.contract_amount or 0),
            "上游完工时间": up_completion_date,
            "上游结算金额": up_settle_amount,
            "上游已收款金额": up_received
        }
        
        # Associated Contracts
        stmt_down = select(ContractDownstream).options(
            selectinload(ContractDownstream.settlements), 
            selectinload(ContractDownstream.payments)
        ).where(ContractDownstream.upstream_contract_id == up.id)
        res_down = await db.execute(stmt_down)
        downs = res_down.scalars().all()
        
        stmt_mgmt = select(ContractManagement).options(
            selectinload(ContractManagement.settlements), 
            selectinload(ContractManagement.payments)
        ).where(ContractManagement.upstream_contract_id == up.id)
        res_mgmt = await db.execute(stmt_mgmt)
        mgmts = res_mgmt.scalars().all()
        
        assoc_list = []
        for d in downs:
            st_amt = 0.0
            if d.settlements:
                st_amt = float(d.settlements[0].settlement_amount or 0)
            pd_amt = sum(float(p.amount or 0) for p in d.payments)
            assoc_list.append({
                "type": "下游合同",
                "serial": d.serial_number,
                "name": d.contract_name,
                "amount": float(d.contract_amount or 0),
                "settle": st_amt,
                "paid": pd_amt
            })
            
        for m in mgmts:
            st_amt = 0.0
            if m.settlements:
                st_amt = float(m.settlements[0].settlement_amount or 0)
            pd_amt = sum(float(p.amount or 0) for p in m.payments)
            assoc_list.append({
                "type": "管理合同",
                "serial": m.serial_number,
                "name": m.contract_name,
                "amount": float(m.contract_amount or 0),
                "settle": st_amt,
                "paid": pd_amt
            })
            
        # Expenses
        stmt_exp = select(ExpenseNonContract).where(ExpenseNonContract.upstream_contract_id == up.id)
        res_exp = await db.execute(stmt_exp)
        exps = res_exp.scalars().all()
        
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
        
        exp_summary = {}
        for e in exps:
            # Group by expense_type (费用分类) and translate to Chinese
            exp_type = e.expense_type or "未分类"
            # Translate from English enum to Chinese
            exp_type_cn = expense_type_map.get(exp_type, exp_type)
            exp_summary[exp_type_cn] = exp_summary.get(exp_type_cn, 0.0) + float(e.amount or 0)
        exp_list = list(exp_summary.items())
        
        # Merge rows
        max_rows = max(len(assoc_list), len(exp_list), 1)
        
        for i in range(max_rows):
            row = base_info.copy()
            
            # Assoc Contract
            if i < len(assoc_list):
                c = assoc_list[i]
                row["下游及管理合同序号"] = c["serial"]
                row["关联-合同名称"] = c["name"]
                row["关联-签约金额"] = c["amount"]
                row["关联-结算金额"] = c["settle"]
                row["关联-已付款金额"] = c["paid"]
            else:
                row["下游及管理合同序号"] = ""
                row["关联-合同名称"] = ""
                row["关联-签约金额"] = ""
                row["关联-结算金额"] = ""
                row["关联-已付款金额"] = ""
                
            # Expense
            if i < len(exp_list):
                cat, amt = exp_list[i]
                row["无合同费用分类"] = cat
                row["无合同费用合计"] = amt
            else:
                row["无合同费用分类"] = ""
                row["无合同费用合计"] = ""
                
            data_list.append(row)
            
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='关联报表')
        worksheet = writer.sheets['关联报表']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    filename = f"上下游合同关联报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_filename = quote(filename)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )
