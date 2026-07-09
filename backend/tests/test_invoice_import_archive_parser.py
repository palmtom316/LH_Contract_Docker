import io
import zipfile
from decimal import Decimal

import pytest

from app.services.invoice_import.archive import UnsafeArchiveError, extract_invoice_archives
from app.services.invoice_import.parser import parse_invoice_xml


def _zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer


def test_rejects_path_traversal(tmp_path):
    nested = _zip_bytes({"../evil.xml": "<xml/>"}).getvalue()
    batch = _zip_bytes({"invoice_001.zip": nested})

    with pytest.raises(UnsafeArchiveError):
        extract_invoice_archives(batch, tmp_path)


def test_extracts_one_invoice_package(tmp_path):
    xml = b"<Invoice><InvoiceNumber>123</InvoiceNumber></Invoice>"
    nested = _zip_bytes({"invoice.xml": xml, "invoice.pdf": b"%PDF-1.4"}).getvalue()
    batch = _zip_bytes({"invoice_001.zip": nested})

    packages = extract_invoice_archives(batch, tmp_path)

    assert len(packages) == 1
    assert packages[0].source_archive_name == "invoice_001.zip"
    assert packages[0].xml_path.name == "invoice.xml"
    assert packages[0].pdf_path.name == "invoice.pdf"


def test_parse_invoice_xml_with_basic_fields():
    xml = """
    <Invoice>
      <InvoiceNumber>INV-001</InvoiceNumber>
      <InvoiceDate>2026-07-08</InvoiceDate>
      <SellerName>供应商A</SellerName>
      <SellerTaxNo>SELLER123</SellerTaxNo>
      <BuyerName>我方公司</BuyerName>
      <BuyerTaxNo>BUYER123</BuyerTaxNo>
      <AmountWithoutTax>100.00</AmountWithoutTax>
      <TaxAmount>6.00</TaxAmount>
      <TotalAmount>106.00</TotalAmount>
      <Remarks>合同 HT-001</Remarks>
    </Invoice>
    """.encode("utf-8")

    parsed = parse_invoice_xml(xml)

    assert parsed.invoice_number == "INV-001"
    assert parsed.invoice_date.isoformat() == "2026-07-08"
    assert parsed.seller_tax_no == "SELLER123"
    assert parsed.buyer_tax_no == "BUYER123"
    assert parsed.total_amount == Decimal("106.00")


def test_parse_invoice_xml_accepts_common_chinese_date_formats():
    parsed_yyyymmdd = parse_invoice_xml(b"<Invoice><Kprq>20240115</Kprq></Invoice>")
    parsed_chinese = parse_invoice_xml("<Invoice><Kprq>2024年01月15日</Kprq></Invoice>".encode("utf-8"))

    assert parsed_yyyymmdd.invoice_date.isoformat() == "2024-01-15"
    assert parsed_chinese.invoice_date.isoformat() == "2024-01-15"


def test_parse_invoice_xml_rejects_xml_entities():
    xml = b"""
    <!DOCTYPE lolz [
      <!ENTITY lol "lol">
      <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
    ]>
    <Invoice><InvoiceNumber>&lol1;</InvoiceNumber></Invoice>
    """

    with pytest.raises(Exception):
        parse_invoice_xml(xml)
