"""
Reports Module - Excel Export Endpoints
Extracted from monolithic reports.py for better maintainability
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, or_, cast, String
from datetime import datetime, date
import logging
import pandas as pd
import io
from urllib.parse import quote

from .summary import _build_cost_report_payload

from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import (
    ContractUpstream, FinanceUpstreamReceipt, FinanceUpstreamReceivable,
    FinanceUpstreamInvoice, ProjectSettlement
)
from app.models.contract_downstream import (
    ContractDownstream, FinanceDownstreamPayment, FinanceDownstreamInvoice,
    FinanceDownstreamPayable, DownstreamSettlement
)
from app.models.contract_management import (
    ContractManagement, FinanceManagementPayment, FinanceManagementInvoice,
    FinanceManagementPayable, ManagementSettlement
)
from app.models.expense import ExpenseNonContract
from app.services.auth import get_current_active_user
from app.core.permissions import require_permission, Permission

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_permission(Permission.DOWNLOAD_REPORTS))])


def _create_excel_response(df: pd.DataFrame, sheet_name: str, filename: str) -> StreamingResponse:
    """Helper to create Excel file response."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max() if not df[col].empty else 0,
                len(str(col))
            ) + 2
            worksheet.set_column(idx, idx, max_len)
    output.seek(0)
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


def _create_excel_multi_sheet_response(sheets: dict[str, pd.DataFrame], filename: str) -> StreamingResponse:
    """Helper to create multi-sheet Excel file response."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        amount_format = workbook.add_format({"num_format": "#,##0.00", "align": "right"})
        amount_columns = {
            "上游合同-签约金额",
            "上游合同-应收款",
            "上游合同-挂账",
            "上游合同-收款",
            "上游合同-结算",
            "下游及管理合同-签约金额",
            "下游及管理合同-应付款",
            "下游及管理合同-挂账",
            "下游及管理合同-付款",
            "下游及管理合同-结算",
            "零星用工",
            "无合同费用",
        }
        for sheet_name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max() if not df[col].empty else 0,
                    len(str(col))
                ) + 2
                col_format = amount_format if col in amount_columns else None
                worksheet.set_column(idx, idx, max_len, col_format)
    output.seek(0)
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


def _build_cost_export_df(rows: list[dict], total: dict) -> pd.DataFrame:
    """Build cost report DataFrame with user-facing Chinese headers."""
    ordered_columns = [
        ("company_category", "公司合同分类"),
        ("upstream_contract_amount", "上游合同-签约金额"),
        ("upstream_receivable", "上游合同-应收款"),
        ("upstream_invoice", "上游合同-挂账"),
        ("upstream_receipt", "上游合同-收款"),
        ("upstream_settlement", "上游合同-结算"),
        ("down_mgmt_contract_amount", "下游及管理合同-签约金额"),
        ("down_mgmt_payable", "下游及管理合同-应付款"),
        ("down_mgmt_invoice", "下游及管理合同-挂账"),
        ("down_mgmt_payment", "下游及管理合同-付款"),
        ("down_mgmt_settlement", "下游及管理合同-结算"),
        ("zero_hour_labor", "零星用工"),
        ("non_contract_expense", "无合同费用"),
    ]

    records = list(rows)
    total_row = dict(total)
    total_row["company_category"] = "合计"
    records.append(total_row)

    result_rows = []
    for row in records:
        result = {}
        for raw_key, header in ordered_columns:
            if raw_key == "company_category":
                result[header] = row.get(raw_key, "")
            else:
                result[header] = float(row.get(raw_key, 0) or 0)
        result_rows.append(result)

    return pd.DataFrame(result_rows)


def _build_comprehensive_row(
    contract: ContractUpstream,
    settlement,
    downstream_totals: dict[str, float],
    management_totals: dict[str, float],
    expense_total: float,
    zero_hour_total: float,
) -> dict:
    return {
        "合同序号": contract.serial_number,
        "合同编号": contract.contract_code,
        "合同名称": contract.contract_name,
        "公司合同分类": contract.company_category or "",
        "合同甲方单位": contract.party_a_name,
        "合同乙方单位": contract.party_b_name,
        "签约时间": contract.sign_date,
        "签约金额": float(contract.contract_amount or 0),
        "完工时间": settlement.completion_date if settlement else None,
        "结算办结时间": settlement.settlement_date if settlement else None,
        "结算金额": float(settlement.settlement_amount or 0) if settlement else 0,
        "累计应收款": sum(float(item.amount or 0) for item in contract.receivables),
        "累计挂账金额": sum(float(item.amount or 0) for item in contract.invoices),
        "累计付款金额": sum(float(item.amount or 0) for item in contract.receipts),
        "关联下游合同结算金额合计": downstream_totals["settlement"],
        "关联下游合同应付款合计": downstream_totals["payable"],
        "关联下游合同已付款合计": downstream_totals["paid"],
        "关联管理合同结算金额合计": management_totals["settlement"],
        "关联管理合同应付款合计": management_totals["payable"],
        "关联管理合同已付款合计": management_totals["paid"],
        "关联无合同费用付款合计": expense_total,
        "关联零星用工费用合计": zero_hour_total,
    }


def _build_association_base_info(
    upstream: ContractUpstream,
    up_completion_date,
    up_settle_amount: float,
    up_received: float,
) -> dict:
    return {
        "上游合同序号": upstream.serial_number,
        "上游合同名称": upstream.contract_name,
        "公司合同分类": upstream.company_category or "",
        "上游签约金额": float(upstream.contract_amount or 0),
        "上游完工时间": up_completion_date,
        "上游结算金额": up_settle_amount,
        "上游已收款金额": up_received,
    }


@router.get("/export/cost/monthly-quarterly")
async def export_cost_monthly_quarterly_report(
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export monthly/quarterly/half-yearly/yearly cost report to a multi-sheet Excel file."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    month = max(1, min(12, int(month)))
    payload = await _build_cost_report_payload(db, year, month)

    monthly_df = _build_cost_export_df(payload["monthly"]["rows"], payload["monthly"]["total"])
    quarterly_df = _build_cost_export_df(payload["quarterly"]["rows"], payload["quarterly"]["total"])
    half_yearly_df = _build_cost_export_df(payload["half_yearly"]["rows"], payload["half_yearly"]["total"])
    yearly_df = _build_cost_export_df(payload["yearly"]["rows"], payload["yearly"]["total"])

    filename = f"成本报表_{year}年{month:02d}月.xlsx"
    return _create_excel_multi_sheet_response(
        {
            "月度成本报表": monthly_df,
            "季度成本报表": quarterly_df,
            "半年度成本报表": half_yearly_df,
            "年度成本报表": yearly_df,
        },
        filename,
    )


@router.get("/export/comprehensive")
async def export_comprehensive_report(
    start_date: date = None,
    end_date: date = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export comprehensive report to Excel"""
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
        df = pd.DataFrame()
        return _create_excel_response(df, '综合报表', 'report.xlsx')

    upstream_ids = [c.id for c in contracts]
    
    async def get_agg(stmt_select):
        res = await db.execute(stmt_select)
        return {r[0]: float(r[1] or 0) for r in res.all()}

    # Downstream Aggregations
    stmt_down_set = select(ContractDownstream.upstream_contract_id, func.sum(DownstreamSettlement.settlement_amount))\
        .join(DownstreamSettlement, DownstreamSettlement.contract_id == ContractDownstream.id)\
        .where(ContractDownstream.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractDownstream.upstream_contract_id)
    map_down_set = await get_agg(stmt_down_set)
    
    stmt_down_pay = select(ContractDownstream.upstream_contract_id, func.sum(FinanceDownstreamInvoice.amount))\
        .join(FinanceDownstreamInvoice, FinanceDownstreamInvoice.contract_id == ContractDownstream.id)\
        .where(ContractDownstream.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractDownstream.upstream_contract_id)
    map_down_pay = await get_agg(stmt_down_pay)
    
    stmt_down_paid = select(ContractDownstream.upstream_contract_id, func.sum(FinanceDownstreamPayment.amount))\
        .join(FinanceDownstreamPayment, FinanceDownstreamPayment.contract_id == ContractDownstream.id)\
        .where(ContractDownstream.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractDownstream.upstream_contract_id)
    map_down_paid = await get_agg(stmt_down_paid)

    # Management Aggregations
    stmt_mgmt_set = select(ContractManagement.upstream_contract_id, func.sum(ManagementSettlement.settlement_amount))\
        .join(ManagementSettlement, ManagementSettlement.contract_id == ContractManagement.id)\
        .where(ContractManagement.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractManagement.upstream_contract_id)
    map_mgmt_set = await get_agg(stmt_mgmt_set)
    
    stmt_mgmt_pay = select(ContractManagement.upstream_contract_id, func.sum(FinanceManagementInvoice.amount))\
        .join(FinanceManagementInvoice, FinanceManagementInvoice.contract_id == ContractManagement.id)\
        .where(ContractManagement.upstream_contract_id.in_(upstream_ids))\
        .group_by(ContractManagement.upstream_contract_id)
    map_mgmt_pay = await get_agg(stmt_mgmt_pay)
    
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

    # Zero Hour Labor Aggregation
    from app.models.zero_hour_labor import ZeroHourLabor
    stmt_zhl = select(ZeroHourLabor.upstream_contract_id, func.sum(ZeroHourLabor.total_amount))\
        .where(ZeroHourLabor.upstream_contract_id.in_(upstream_ids))\
        .group_by(ZeroHourLabor.upstream_contract_id)
    map_zhl = await get_agg(stmt_zhl)

    # Assemble Data
    data_list = []
    for c in contracts:
        settlement = c.settlements[0] if c.settlements else None
        downstream_totals = {
            "settlement": map_down_set.get(c.id, 0),
            "payable": map_down_pay.get(c.id, 0),
            "paid": map_down_paid.get(c.id, 0),
        }
        management_totals = {
            "settlement": map_mgmt_set.get(c.id, 0),
            "payable": map_mgmt_pay.get(c.id, 0),
            "paid": map_mgmt_paid.get(c.id, 0),
        }
        row = _build_comprehensive_row(
            c,
            settlement,
            downstream_totals=downstream_totals,
            management_totals=management_totals,
            expense_total=map_exp.get(c.id, 0),
            zero_hour_total=map_zhl.get(c.id, 0),
        )
        data_list.append(row)
        
    df = pd.DataFrame(data_list)
    
    date_cols = ["签约时间", "完工时间", "结算办结时间"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
    
    filename = f"综合报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '综合报表', filename)


@router.get("/export/receivables")
async def export_receivables(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Upstream Receivables"""
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
            "备注": rec.description or ""
        })
        
    df = pd.DataFrame(data_list)
    filename = f"上游合同应收款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '应收款明细', filename)


@router.get("/export/payables")
async def export_payables(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Downstream/Management Payables"""
    data_list = []
    idx_counter = 1
    
    # Downstream
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
        
    # Management
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
    if not df.empty and '应付日期' in df.columns:
        df['应付日期'] = pd.to_datetime(df['应付日期'])
        df = df.sort_values(by='应付日期', ascending=False)
        df['应付日期'] = df['应付日期'].dt.date
    
    filename = f"应付款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '应付款明细', filename)


@router.get("/export/invoices/upstream")
async def export_upstream_invoices(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Upstream Invoices (Guazhang)"""
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
    filename = f"上游合同挂账报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '挂账明细', filename)


@router.get("/export/invoices/downstream")
async def export_downstream_invoices(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Downstream/Management Invoices (Guazhang)"""
    data_list = []
    idx_counter = 1
    
    # Downstream
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
        
    # Management
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
    if not df.empty and '挂账日期' in df.columns:
        df['挂账日期'] = pd.to_datetime(df['挂账日期'])
        df = df.sort_values(by='挂账日期', ascending=False)
        df['挂账日期'] = df['挂账日期'].dt.date
    
    filename = f"下游及管理合同挂账报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '挂账明细', filename)


@router.get("/export/receipts/upstream")
async def export_upstream_receipts(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Upstream Receipts (实际收款)"""
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
    filename = f"上游合同收款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '收款明细', filename)


@router.get("/export/payments/downstream")
async def export_downstream_payments(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Downstream/Management Payments (实际付款)"""
    data_list = []
    idx_counter = 1
    
    # Downstream
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
        
    # Management
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
    if not df.empty and '付款日期' in df.columns:
        df['付款日期'] = pd.to_datetime(df['付款日期'])
        df = df.sort_values(by='付款日期', ascending=False)
        df['付款日期'] = df['付款日期'].dt.date
    
    filename = f"下游及管理合同付款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '付款明细', filename)


@router.get("/export/payments/expenses")
async def export_expense_payments(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Non-Contract Expense Payments (无合同费用) including Zero Hour Labor"""
    stmt = select(ExpenseNonContract).options(selectinload(ExpenseNonContract.upstream_contract))
    
    if start_date:
        stmt = stmt.where(ExpenseNonContract.expense_date >= start_date)
    if end_date:
        stmt = stmt.where(ExpenseNonContract.expense_date <= end_date)
    
    stmt = stmt.order_by(ExpenseNonContract.expense_date.desc())
    
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
    data_list = []
    idx = 1
    for exp in rows:
        data_list.append({
            "序号": idx,
            "费用类型": "无合同费用",
            "费用归属": exp.attribution or "",
            "费用类别": exp.category or "",
            "费用分类": exp.expense_type or "",
            "关联上游合同": exp.upstream_contract.contract_name if exp.upstream_contract else "",
            "发生日期": exp.expense_date,
            "金额": float(exp.amount or 0),
            "经办人": exp.handler or "",
            "说明": exp.description or ""
        })
        idx += 1
    
    # Zero Hour Labor
    from app.models.zero_hour_labor import ZeroHourLabor
    from sqlalchemy.orm import selectinload as sl
    
    stmt_zhl = select(ZeroHourLabor).options(sl(ZeroHourLabor.upstream_contract))
    
    if start_date:
        stmt_zhl = stmt_zhl.where(ZeroHourLabor.labor_date >= start_date)
    if end_date:
        stmt_zhl = stmt_zhl.where(ZeroHourLabor.labor_date <= end_date)
    
    stmt_zhl = stmt_zhl.order_by(ZeroHourLabor.labor_date.desc())
    
    result_zhl = await db.execute(stmt_zhl)
    rows_zhl = result_zhl.scalars().all()
    
    for zhl in rows_zhl:
        data_list.append({
            "序号": idx,
            "费用类型": "零星用工",
            "费用归属": "项目用工" if zhl.attribution == "PROJECT" else "公司用工",
            "费用类别": "零星用工",
            "费用分类": "零星用工",
            "关联上游合同": zhl.upstream_contract.contract_name if zhl.upstream_contract else "",
            "发生日期": zhl.labor_date,
            "金额": float(zhl.total_amount or 0),
            "经办人": zhl.dispatch_unit or "",
            "说明": f"技工{zhl.skilled_quantity or 0}人,普工{zhl.general_quantity or 0}人"
        })
        idx += 1
        
    df = pd.DataFrame(data_list)
    filename = f"无合同费用付款报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '费用明细', filename)


@router.get("/export/settlements/upstream")
async def export_upstream_settlements(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Upstream Settlements (项目结算)"""
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
    filename = f"上游合同结算报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '结算明细', filename)


@router.get("/export/settlements/downstream")
async def export_downstream_settlements(
    start_date: date = None,
    end_date: date = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Downstream/Management Settlements (结算记录)"""
    data_list = []
    idx_counter = 1
    
    # Downstream
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
        
    # Management
    stmt_mgmt = select(ManagementSettlement, ContractManagement).join(ContractManagement)
    if start_date:
        stmt_mgmt = stmt_mgmt.where(ManagementSettlement.settlement_date >= start_date)
    if end_date:
        stmt_mgmt = stmt_mgmt.where(ManagementSettlement.settlement_date >= end_date)
        
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
    if not df.empty and '结算日期' in df.columns:
        df['结算日期'] = pd.to_datetime(df['结算日期'])
        df = df.sort_values(by='结算日期', ascending=False)
        df['结算日期'] = df['结算日期'].dt.date
    
    filename = f"下游及管理合同结算报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '结算明细', filename)


@router.get("/export/association")
async def export_association_report(
    query: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Upstream-Downstream Association Report"""
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
        up_settle_amount = 0.0
        up_completion_date = None
        if up.settlements:
            latest = sorted(up.settlements, key=lambda x: x.settlement_date or date.min, reverse=True)[0]
            up_settle_amount = float(latest.settlement_amount or 0)
            up_completion_date = latest.completion_date
             
        up_received = sum(float(r.amount or 0) for r in up.receipts)
        base_info = _build_association_base_info(
            up,
            up_completion_date=up_completion_date,
            up_settle_amount=up_settle_amount,
            up_received=up_received,
        )
        
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
                "type": "下游合同", "serial": d.serial_number, "name": d.contract_name,
                "amount": float(d.contract_amount or 0), "settle": st_amt, "paid": pd_amt
            })
            
        for m in mgmts:
            st_amt = 0.0
            if m.settlements:
                st_amt = float(m.settlements[0].settlement_amount or 0)
            pd_amt = sum(float(p.amount or 0) for p in m.payments)
            assoc_list.append({
                "type": "管理合同", "serial": m.serial_number, "name": m.contract_name,
                "amount": float(m.contract_amount or 0), "settle": st_amt, "paid": pd_amt
            })
            
        # Expenses
        stmt_exp = select(ExpenseNonContract).where(ExpenseNonContract.upstream_contract_id == up.id)
        res_exp = await db.execute(stmt_exp)
        exps = res_exp.scalars().all()
        
        expense_type_map = {
            "MANAGEMENT": "管理费", "TRAINING": "培训费", "CATERING": "餐饮费",
            "TRANSPORT": "交通费", "CONSULTING": "咨询费", "BUSINESS": "业务费",
            "LEASING": "租赁费", "QUALIFICATION": "资质费", "VEHICLE": "车辆使用费"
        }
        
        exp_summary = {}
        for e in exps:
            exp_type = e.expense_type or "未分类"
            exp_type_cn = expense_type_map.get(exp_type, exp_type)
            exp_summary[exp_type_cn] = exp_summary.get(exp_type_cn, 0.0) + float(e.amount or 0)
        
        # Zero Hour Labor
        from app.models.zero_hour_labor import ZeroHourLabor
        stmt_zhl = select(ZeroHourLabor).where(ZeroHourLabor.upstream_contract_id == up.id)
        res_zhl = await db.execute(stmt_zhl)
        zhls = res_zhl.scalars().all()
        
        if zhls:
            zhl_total = sum(float(z.total_amount or 0) for z in zhls)
            exp_summary["零星用工"] = exp_summary.get("零星用工", 0.0) + zhl_total
            
        exp_list = list(exp_summary.items())
        
        max_rows = max(len(assoc_list), len(exp_list), 1)
        
        for i in range(max_rows):
            row = base_info.copy()
            
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
                
            if i < len(exp_list):
                cat, amt = exp_list[i]
                row["无合同费用分类"] = cat
                row["无合同费用合计"] = amt
            else:
                row["无合同费用分类"] = ""
                row["无合同费用合计"] = ""
                
            data_list.append(row)
            
    df = pd.DataFrame(data_list)
    filename = f"上下游合同关联报表_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return _create_excel_response(df, '关联报表', filename)
