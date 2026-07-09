"""Direction, dedupe, and candidate matching for imported invoices."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_downstream import ContractDownstream
from app.models.contract_upstream import ContractUpstream
from app.models.invoice_import import InvoiceImportItem, InvoiceImportMatchCandidate
from app.services.invoice_import.parser import ParsedInvoice


def _norm(value: object) -> str:
    return str(value or "").strip()


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
        query = select(ContractUpstream).where(
            or_(
                ContractUpstream.party_a_tax_no == item.buyer_tax_no,
                ContractUpstream.party_a_name.ilike(f"%{item.buyer_name or ''}%"),
                ContractUpstream.contract_code.ilike(f"%{item.remarks or ''}%"),
            )
        ).limit(20)
        result = await self.db.execute(query)
        candidates = []
        for contract in result.scalars().all():
            score = 0
            signals = {}
            if item.buyer_tax_no and contract.party_a_tax_no == item.buyer_tax_no:
                score += 70
                signals["party_a_tax_no"] = True
            name_score = self._text_score(item.buyer_name, contract.party_a_name, 25)
            if name_score:
                score += name_score
                signals["party_a_name"] = name_score
            keyword_text = " ".join([item.remarks or "", contract.contract_code or "", contract.contract_name or "", contract.project_name or ""])
            keyword_score = self._text_score(contract.contract_code, keyword_text, 20)
            if keyword_score:
                score += keyword_score
                signals["contract_code"] = keyword_score
            candidates.append(InvoiceImportMatchCandidate(item_id=item.id, direction="upstream", upstream_contract_id=contract.id, score=score, matched_signals=signals))
        return sorted(candidates, key=lambda c: c.score, reverse=True)

    async def _find_downstream_candidates(self, item: InvoiceImportItem) -> List[InvoiceImportMatchCandidate]:
        query = select(ContractDownstream).where(
            or_(
                ContractDownstream.party_b_tax_no == item.seller_tax_no,
                ContractDownstream.party_b_name.ilike(f"%{item.seller_name or ''}%"),
                ContractDownstream.contract_code.ilike(f"%{item.remarks or ''}%"),
            )
        ).limit(20)
        result = await self.db.execute(query)
        candidates = []
        for contract in result.scalars().all():
            score = 0
            signals = {}
            if item.seller_tax_no and contract.party_b_tax_no == item.seller_tax_no:
                score += 70
                signals["party_b_tax_no"] = True
            name_score = self._text_score(item.seller_name, contract.party_b_name, 25)
            if name_score:
                score += name_score
                signals["party_b_name"] = name_score
            keyword_text = " ".join([item.remarks or "", contract.contract_code or "", contract.contract_name or ""])
            keyword_score = self._text_score(contract.contract_code, keyword_text, 20)
            if keyword_score:
                score += keyword_score
                signals["contract_code"] = keyword_score
            candidates.append(InvoiceImportMatchCandidate(item_id=item.id, direction="downstream", downstream_contract_id=contract.id, score=score, matched_signals=signals))
        return sorted(candidates, key=lambda c: c.score, reverse=True)
