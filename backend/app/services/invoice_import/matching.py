"""Direction, dedupe, and candidate matching for imported invoices."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from sqlalchemy import or_, select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_downstream import ContractDownstream
from app.models.contract_upstream import ContractUpstream
from app.models.invoice_import import InvoiceImportItem, InvoiceImportMatchCandidate
from app.services.invoice_import.parser import ParsedInvoice


def _norm(value: object) -> str:
    return str(value or "").strip()


def _like_pattern(value: object) -> str | None:
    text = _norm(value)
    if not text:
        return None
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _or_nonempty(*conditions: tuple[object, ColumnElement[bool]]) -> ColumnElement[bool] | None:
    active = [condition for raw_value, condition in conditions if _norm(raw_value)]
    return or_(*active) if active else None


def build_dedupe_key(parsed: ParsedInvoice) -> str:
    invoice_date = parsed.invoice_date.isoformat() if parsed.invoice_date else ""
    total = parsed.total_amount.quantize(Decimal("0.01")) if parsed.total_amount is not None else Decimal("0.00")
    return "|".join([
        _norm(parsed.invoice_number),
        _norm(parsed.seller_tax_no),
        _norm(parsed.buyer_tax_no),
        invoice_date,
        f"{total:.2f}",
    ])


def detect_direction(parsed: ParsedInvoice, company_tax_no: str) -> str:
    company = _norm(company_tax_no)
    seller = _norm(parsed.seller_tax_no)
    buyer = _norm(parsed.buyer_tax_no)
    if seller == company and buyer != company:
        return "upstream"
    if buyer == company and seller != company:
        return "downstream"
    return "unknown"


class InvoiceMatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _text_score(self, needle: str, haystack: str, points: int) -> int:
        needle_value = _norm(needle)
        haystack_value = _norm(haystack)
        if needle_value and haystack_value and needle_value in haystack_value:
            return points
        if needle_value and haystack_value and haystack_value in needle_value:
            return max(points - 10, 0)
        return 0

    async def find_candidates(self, item: InvoiceImportItem) -> List[InvoiceImportMatchCandidate]:
        if item.direction == "upstream":
            return await self._find_upstream_candidates(item)
        if item.direction == "downstream":
            return await self._find_downstream_candidates(item)
        return []

    async def _find_upstream_candidates(self, item: InvoiceImportItem) -> List[InvoiceImportMatchCandidate]:
        project_name = item.construction_project_name or item.project_name
        project_pattern = _like_pattern(project_name)
        buyer_name_pattern = _like_pattern(item.buyer_name)
        remarks_pattern = _like_pattern(item.remarks)
        query = None
        if project_pattern:
            query = select(ContractUpstream).where(
                ContractUpstream.contract_name.ilike(project_pattern, escape="\\")
            ).limit(20)
        result = await self.db.execute(query) if query is not None else None
        contracts = list(result.scalars().all()) if result is not None else []
        if project_pattern and not contracts:
            return []
        if not project_pattern:
            predicate = _or_nonempty(
                (item.buyer_tax_no, ContractUpstream.party_a_tax_no == item.buyer_tax_no),
                (
                    item.buyer_name,
                    ContractUpstream.party_a_name.ilike(buyer_name_pattern, escape="\\")
                    if buyer_name_pattern else None,
                ),
                (
                    item.remarks,
                    ContractUpstream.contract_code.ilike(remarks_pattern, escape="\\")
                    if remarks_pattern else None,
                ),
            )
            if predicate is None:
                return []
            result = await self.db.execute(select(ContractUpstream).where(predicate).limit(100))
            contracts = list(result.scalars().all())
        candidates = []
        for contract in contracts:
            score = 0
            signals = {}
            project_score = self._text_score(project_name, contract.contract_name, 100)
            if project_score:
                score += project_score
                signals["construction_project_name"] = project_score
            if item.buyer_tax_no and contract.party_a_tax_no == item.buyer_tax_no:
                score += 20
                signals["party_a_tax_no"] = True
            name_score = self._text_score(item.buyer_name, contract.party_a_name, 10)
            if name_score:
                score += name_score
                signals["party_a_name"] = name_score
            keyword_score = self._text_score(contract.contract_code, item.remarks or "", 10)
            if keyword_score:
                score += keyword_score
                signals["contract_code"] = keyword_score
            candidates.append(InvoiceImportMatchCandidate(
                item_id=item.id,
                direction="upstream",
                upstream_contract_id=contract.id,
                score=score,
                matched_signals=signals,
            ))
        return sorted(candidates, key=lambda c: c.score, reverse=True)

    async def _find_downstream_candidates(self, item: InvoiceImportItem) -> List[InvoiceImportMatchCandidate]:
        project_name = item.construction_project_name or item.project_name
        project_pattern = _like_pattern(project_name)
        seller_name_pattern = _like_pattern(item.seller_name)
        remarks_pattern = _like_pattern(item.remarks)
        query = None
        if project_pattern:
            query = select(ContractDownstream).where(
                ContractDownstream.contract_name.ilike(project_pattern, escape="\\")
            ).limit(20)
        result = await self.db.execute(query) if query is not None else None
        contracts = list(result.scalars().all()) if result is not None else []
        if project_pattern and not contracts:
            return []
        if not project_pattern:
            predicate = _or_nonempty(
                (item.seller_tax_no, ContractDownstream.party_b_tax_no == item.seller_tax_no),
                (
                    item.seller_name,
                    ContractDownstream.party_b_name.ilike(seller_name_pattern, escape="\\")
                    if seller_name_pattern else None,
                ),
                (
                    item.remarks,
                    ContractDownstream.contract_code.ilike(remarks_pattern, escape="\\")
                    if remarks_pattern else None,
                ),
            )
            if predicate is None:
                return []
            result = await self.db.execute(select(ContractDownstream).where(predicate).limit(100))
            contracts = list(result.scalars().all())
        candidates = []
        for contract in contracts:
            score = 0
            signals = {}
            project_score = self._text_score(project_name, contract.contract_name, 100)
            if project_score:
                score += project_score
                signals["construction_project_name"] = project_score
            if item.seller_tax_no and contract.party_b_tax_no == item.seller_tax_no:
                score += 20
                signals["party_b_tax_no"] = True
            name_score = self._text_score(item.seller_name, contract.party_b_name, 10)
            if name_score:
                score += name_score
                signals["party_b_name"] = name_score
            keyword_score = self._text_score(contract.contract_code, item.remarks or "", 10)
            if keyword_score:
                score += keyword_score
                signals["contract_code"] = keyword_score
            candidates.append(InvoiceImportMatchCandidate(
                item_id=item.id,
                direction="downstream",
                downstream_contract_id=contract.id,
                score=score,
                matched_signals=signals,
            ))
        return sorted(candidates, key=lambda c: c.score, reverse=True)
