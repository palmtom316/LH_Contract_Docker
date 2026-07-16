"""XML parser for electronic invoice import."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import re
from decimal import Decimal
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET
try:
    from defusedxml.ElementTree import ParseError, fromstring as safe_xml_fromstring
except ImportError:  # pragma: no cover - dependency fallback for constrained installs
    from xml.etree.ElementTree import ParseError

    def safe_xml_fromstring(xml_bytes: bytes):
        if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
            raise ParseError("XML entities and DOCTYPE declarations are not allowed")
        return ET.fromstring(xml_bytes)


@dataclass(frozen=True)
class ParsedInvoice:
    invoice_number: Optional[str]
    invoice_code: Optional[str]
    invoice_date: Optional[date]
    seller_name: Optional[str]
    seller_tax_no: Optional[str]
    buyer_name: Optional[str]
    buyer_tax_no: Optional[str]
    amount_without_tax: Optional[Decimal]
    tax_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    invoice_type: Optional[str]
    remarks: Optional[str]
    payload: Dict[str, Any] = field(default_factory=dict)


ALIASES = {
    "invoice_number": ["InvoiceNumber", "InvoiceNo", "Fphm", "FpHm"],
    "invoice_code": ["InvoiceCode", "Fpdm", "FpDm"],
    "invoice_date": ["InvoiceDate", "Kprq", "IssueDate"],
    "seller_name": ["SellerName", "XsfMc", "Seller"],
    "seller_tax_no": ["SellerTaxNo", "XsfNsrsbh", "SellerTaxID"],
    "buyer_name": ["BuyerName", "GmfMc", "Buyer"],
    "buyer_tax_no": ["BuyerTaxNo", "GmfNsrsbh", "BuyerTaxID"],
    "amount_without_tax": ["AmountWithoutTax", "Hjje", "Amount"],
    "tax_amount": ["TaxAmount", "Hjse", "Tax"],
    "total_amount": ["TotalAmount", "Jshj", "Total"],
    "invoice_type": ["InvoiceType", "Fplx"],
    "remarks": ["Remarks", "Bz", "Memo"],
}


def _text_by_alias(root: ET.Element, aliases: list[str]) -> Optional[str]:
    aliases_set = set(aliases)
    for node in root.iter():
        local_name = node.tag.rsplit("}", 1)[-1] if isinstance(node.tag, str) else ""
        if local_name in aliases_set and node.text and node.text.strip():
            return node.text.strip()
    return None


def _to_decimal(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None
    return Decimal(value.replace(",", "").strip()).quantize(Decimal("0.01"))


def _to_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None

    # Common Chinese e-invoice formats include YYYYMMDD and YYYY年MM月DD日.
    compact = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", normalized)
    if compact:
        year, month, day = compact.groups()
        return date(int(year), int(month), int(day))

    chinese = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", normalized)
    if chinese:
        year, month, day = chinese.groups()
        return date(int(year), int(month), int(day))

    normalized = normalized.replace("/", "-").replace(".", "-")
    iso_prefix = re.match(r"\d{4}-\d{1,2}-\d{1,2}", normalized)
    if iso_prefix:
        year, month, day = iso_prefix.group(0).split("-")
        return date(int(year), int(month), int(day))
    return date.fromisoformat(normalized[:10])


def parse_invoice_xml(xml_bytes: bytes) -> ParsedInvoice:
    root = safe_xml_fromstring(xml_bytes)
    values = {key: _text_by_alias(root, aliases) for key, aliases in ALIASES.items()}
    payload = {key: value for key, value in values.items() if value is not None}

    return ParsedInvoice(
        invoice_number=values["invoice_number"],
        invoice_code=values["invoice_code"],
        invoice_date=_to_date(values["invoice_date"]),
        seller_name=values["seller_name"],
        seller_tax_no=values["seller_tax_no"],
        buyer_name=values["buyer_name"],
        buyer_tax_no=values["buyer_tax_no"],
        amount_without_tax=_to_decimal(values["amount_without_tax"]),
        tax_amount=_to_decimal(values["tax_amount"]),
        total_amount=_to_decimal(values["total_amount"]),
        invoice_type=values["invoice_type"],
        remarks=values["remarks"],
        payload=payload,
    )
