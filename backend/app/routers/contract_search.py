"""
Contract Search Router (合同查询机器人后端)
提供合同模糊搜索和关联信息查询功能
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, and_, cast, String
from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.services.auth import get_current_active_user
from app.models.user import User
from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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
    summary: Optional[SearchSummary] = None


@router.get("/search", response_model=SearchResponse)
async def search_contracts(
    query: str = Query("", description="搜索关键词（合同序号、名称或编号）"),
    company_category: str = Query("", description="公司合同分类"),
    party_a_name: str = Query("", description="上游合同甲方单位"),
    party_b_name: str = Query("", description="下游/管理合同乙方单位"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制"),
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
        limit: 返回结果数量限制
        
    Returns:
        匹配的上游合同列表，包含财务汇总和关联合同信息
    """
    # Normalize inputs
    query = (query or "").strip()
    company_category = (company_category or "").strip()
    party_a_name = (party_a_name or "").strip()
    party_b_name = (party_b_name or "").strip()
    has_party_a = bool(party_a_name)
    has_party_b = bool(party_b_name)

    # Build query conditions
    conditions = []
    
    # Text search condition (query)
    if query:
        conditions.append(
            or_(
                ContractUpstream.contract_code.ilike(f"%{query}%"),
                ContractUpstream.contract_name.ilike(f"%{query}%"),
                cast(ContractUpstream.serial_number, String).ilike(f"%{query}%")
            )
        )
    
    # Company category filter
    if company_category:
        conditions.append(ContractUpstream.company_category.ilike(f"%{company_category}%"))

    # Party A filter (Upstream)
    if has_party_a:
        conditions.append(ContractUpstream.party_a_name.ilike(f"%{party_a_name}%"))

    # Party B filter (Downstream/Management)
    if has_party_b:
        party_b_condition = or_(
            ContractUpstream.id.in_(
                select(ContractDownstream.upstream_contract_id).where(
                    ContractDownstream.party_b_name.ilike(f"%{party_b_name}%")
                )
            ),
            ContractUpstream.id.in_(
                select(ContractManagement.upstream_contract_id).where(
                    ContractManagement.party_b_name.ilike(f"%{party_b_name}%")
                )
            )
        )
        conditions.append(party_b_condition)
    
    # At least one condition is required
    if not conditions:
        return SearchResponse(total=0, results=[], summary=None)
    
    # Query upstream contracts with fuzzy matching
    stmt = select(ContractUpstream).options(
        selectinload(ContractUpstream.receivables),
        selectinload(ContractUpstream.invoices),
        selectinload(ContractUpstream.receipts),
        selectinload(ContractUpstream.settlements)
    ).where(and_(*conditions)).order_by(ContractUpstream.serial_number.desc().nulls_last()).limit(limit)
    
    result = await db.execute(stmt)
    upstream_contracts = result.scalars().all()
    
    results = []
    party_a_totals = {
        "contract_amount": 0.0,
        "payable_amount": 0.0,
        "invoiced_amount": 0.0,
        "paid_amount": 0.0
    }
    party_b_totals = {
        "contract_amount": 0.0,
        "payable_amount": 0.0,
        "invoiced_amount": 0.0,
        "paid_amount": 0.0
    }
    party_a_count = 0
    party_b_count = 0
    
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
    
    for up in upstream_contracts:
        # Calculate upstream finance summary
        # 应收款 = sum of receivables
        receivable_total = sum(float(r.amount or 0) for r in up.receivables)
        # 挂账金额 = sum of invoices
        invoiced_total = sum(float(i.amount or 0) for i in up.invoices)
        # 已收款 = sum of receipts
        received_total = sum(float(r.amount or 0) for r in up.receipts)
        
        up_finance = FinanceSummary(
            contract_amount=float(up.contract_amount or 0),
            payable_amount=receivable_total,  # 对于上游合同，应收款 = 应付方的应付
            invoiced_amount=invoiced_total,
            paid_amount=received_total
        )

        if has_party_a:
            party_a_count += 1
            party_a_totals["contract_amount"] += up_finance.contract_amount
            party_a_totals["payable_amount"] += up_finance.payable_amount
            party_a_totals["invoiced_amount"] += up_finance.invoiced_amount
            party_a_totals["paid_amount"] += up_finance.paid_amount
        
        # Get associated downstream contracts
        stmt_down = select(ContractDownstream).options(
            selectinload(ContractDownstream.payables),
            selectinload(ContractDownstream.invoices),
            selectinload(ContractDownstream.payments),
            selectinload(ContractDownstream.settlements)
        ).where(ContractDownstream.upstream_contract_id == up.id)
        if has_party_b:
            stmt_down = stmt_down.where(ContractDownstream.party_b_name.ilike(f"%{party_b_name}%"))
        
        res_down = await db.execute(stmt_down)
        downs = res_down.scalars().all()
        
        downstream_list = []
        for d in downs:
            d_payable = sum(float(p.amount or 0) for p in d.payables)
            d_invoiced = sum(float(i.amount or 0) for i in d.invoices)
            d_paid = sum(float(p.amount or 0) for p in d.payments)
            
            downstream_list.append(AssociatedContract(
                id=d.id,
                serial_number=d.serial_number,
                contract_code=d.contract_code,
                contract_name=d.contract_name,
                party_b_name=d.party_b_name,
                contract_type="downstream",
                finance=FinanceSummary(
                    contract_amount=float(d.contract_amount or 0),
                    payable_amount=d_payable,
                    invoiced_amount=d_invoiced,
                    paid_amount=d_paid
                )
            ))

            if has_party_b:
                party_b_count += 1
                party_b_totals["contract_amount"] += float(d.contract_amount or 0)
                party_b_totals["payable_amount"] += d_payable
                party_b_totals["invoiced_amount"] += d_invoiced
                party_b_totals["paid_amount"] += d_paid
        
        # Get associated management contracts
        stmt_mgmt = select(ContractManagement).options(
            selectinload(ContractManagement.payables),
            selectinload(ContractManagement.invoices),
            selectinload(ContractManagement.payments),
            selectinload(ContractManagement.settlements)
        ).where(ContractManagement.upstream_contract_id == up.id)
        if has_party_b:
            stmt_mgmt = stmt_mgmt.where(ContractManagement.party_b_name.ilike(f"%{party_b_name}%"))
        
        res_mgmt = await db.execute(stmt_mgmt)
        mgmts = res_mgmt.scalars().all()
        
        management_list = []
        for m in mgmts:
            m_payable = sum(float(p.amount or 0) for p in m.payables)
            m_invoiced = sum(float(i.amount or 0) for i in m.invoices)
            m_paid = sum(float(p.amount or 0) for p in m.payments)
            
            management_list.append(AssociatedContract(
                id=m.id,
                serial_number=m.serial_number,
                contract_code=m.contract_code,
                contract_name=m.contract_name,
                party_b_name=m.party_b_name,
                contract_type="management",
                finance=FinanceSummary(
                    contract_amount=float(m.contract_amount or 0),
                    payable_amount=m_payable,
                    invoiced_amount=m_invoiced,
                    paid_amount=m_paid
                )
            ))

            if has_party_b:
                party_b_count += 1
                party_b_totals["contract_amount"] += float(m.contract_amount or 0)
                party_b_totals["payable_amount"] += m_payable
                party_b_totals["invoiced_amount"] += m_invoiced
                party_b_totals["paid_amount"] += m_paid
        
        # Get associated expenses (无合同费用)
        stmt_exp = select(ExpenseNonContract).where(
            ExpenseNonContract.upstream_contract_id == up.id
        )
        res_exp = await db.execute(stmt_exp)
        exps = res_exp.scalars().all()
        
        exp_summary = {}
        for e in exps:
            exp_type = e.expense_type or "未分类"
            exp_type_cn = expense_type_map.get(exp_type, exp_type)
            exp_summary[exp_type_cn] = exp_summary.get(exp_type_cn, 0.0) + float(e.amount or 0)
        
        # Get zero hour labor
        stmt_zhl = select(ZeroHourLabor).where(
            ZeroHourLabor.upstream_contract_id == up.id
        )
        res_zhl = await db.execute(stmt_zhl)
        zhls = res_zhl.scalars().all()
        
        if zhls:
            zhl_total = sum(float(z.total_amount or 0) for z in zhls)
            exp_summary["零星用工"] = exp_summary.get("零星用工", 0.0) + zhl_total
        
        expenses_list = [
            ExpenseCategory(category=cat, amount=amt)
            for cat, amt in exp_summary.items()
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
    
    summary = None
    if results and (has_party_a or has_party_b):
        summary = SearchSummary(
            party_a=PartySummary(
                party_name=party_a_name,
                contract_count=party_a_count,
                finance=FinanceSummary(**party_a_totals)
            ) if has_party_a else None,
            party_b=PartySummary(
                party_name=party_b_name,
                contract_count=party_b_count,
                finance=FinanceSummary(**party_b_totals)
            ) if has_party_b else None
        )

    return SearchResponse(
        total=len(results),
        results=results,
        summary=summary
    )
