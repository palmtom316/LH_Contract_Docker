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


def _compressed_zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
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


def test_extracts_tax_authority_single_invoice_archive(tmp_path):
    archive = _zip_bytes({
        "dzfp_package/invoice.xml": b"<EInvoice><InvoiceNumber>26502000001442925721</InvoiceNumber></EInvoice>",
        "dzfp_package/invoice.pdf": b"%PDF-1.4",
    })

    packages = extract_invoice_archives(archive, tmp_path, "dzfp_26502000001442925721.zip")

    assert len(packages) == 1
    assert packages[0].source_archive_name == "dzfp_26502000001442925721.zip"
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


def test_parse_invoice_xml_accepts_namespaced_fields():
    xml = b"""
    <Invoice xmlns="urn:cn:invoice">
      <InvoiceNumber>NS-001</InvoiceNumber>
      <SellerTaxNo>SELLER-NS</SellerTaxNo>
      <TotalAmount>106.00</TotalAmount>
    </Invoice>
    """

    parsed = parse_invoice_xml(xml)

    assert parsed.invoice_number == "NS-001"
    assert parsed.seller_tax_no == "SELLER-NS"
    assert parsed.total_amount == Decimal("106.00")


def test_parse_invoice_xml_accepts_digital_invoice_fields():
    xml = """
    <EInvoice>
      <Header>
        <InherentLabel>
          <GeneralOrSpecialVAT><LabelName>增值税专用发票</LabelName></GeneralOrSpecialVAT>
        </InherentLabel>
      </Header>
      <EInvoiceData>
        <SellerInformation>
          <SellerIdNum>91500107057774330E</SellerIdNum>
          <SellerName>重庆蓝海电力工程有限责任公司</SellerName>
        </SellerInformation>
        <BuyerInformation>
          <BuyerIdNum>91500000902846312Y</BuyerIdNum>
          <BuyerName>国网重庆市电力公司市区供电分公司</BuyerName>
        </BuyerInformation>
        <BasicInformation>
          <TotalAmWithoutTax>609724.77</TotalAmWithoutTax>
          <TotalTaxAm>54875.23</TotalTaxAm>
          <TotalTax-includedAmount>664600.00</TotalTax-includedAmount>
        </BasicInformation>
        <IssuItemInformation>
          <MeaUnits>重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程</MeaUnits>
        </IssuItemInformation>
        <SpecificInformation>
          <ConstructionServices>
            <ItemName>重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程</ItemName>
          </ConstructionServices>
        </SpecificInformation>
      </EInvoiceData>
      <TaxSupervisionInfo>
        <InvoiceNumber>26502000001442925721</InvoiceNumber>
        <IssueTime>2026-07-16</IssueTime>
      </TaxSupervisionInfo>
    </EInvoice>
    """.encode("utf-8")

    parsed = parse_invoice_xml(xml)

    assert parsed.invoice_number == "26502000001442925721"
    assert parsed.invoice_date.isoformat() == "2026-07-16"
    assert parsed.seller_tax_no == "91500107057774330E"
    assert parsed.buyer_tax_no == "91500000902846312Y"
    assert parsed.amount_without_tax == Decimal("609724.77")
    assert parsed.tax_amount == Decimal("54875.23")
    assert parsed.total_amount == Decimal("664600.00")
    assert parsed.invoice_type == "增值税专用发票"
    assert parsed.project_name == "重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程"
    assert parsed.construction_project_name == "重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程"


def test_rejects_batch_with_excessive_cumulative_expanded_size(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.invoice_import.archive.settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE", 2000)
    first = _compressed_zip_bytes({"invoice.xml": b"A" * 1200}).getvalue()
    second = _compressed_zip_bytes({"invoice.xml": b"B" * 1200}).getvalue()
    batch = _zip_bytes({"invoice_001.zip": first, "invoice_002.zip": second})

    with pytest.raises(UnsafeArchiveError, match="recursive expanded size"):
        extract_invoice_archives(batch, tmp_path)


def test_rejects_batch_with_too_many_members(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.invoice_import.archive.settings.INVOICE_IMPORT_MAX_FILES", 1)
    nested = _zip_bytes({"invoice.xml": b"<Invoice/>"}).getvalue()
    batch = _zip_bytes({"invoice_001.zip": nested, "invoice_002.zip": nested})

    with pytest.raises(UnsafeArchiveError, match="too many files"):
        extract_invoice_archives(batch, tmp_path)


def test_rejects_excessive_recursive_member_count(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.invoice_import.archive.settings.INVOICE_IMPORT_MAX_FILES", 3)
    first = _zip_bytes({"invoice.xml": b"<Invoice/>", "invoice.pdf": b"pdf"}).getvalue()
    second = _zip_bytes({"invoice.xml": b"<Invoice/>", "invoice.ofd": b"ofd"}).getvalue()
    batch = _zip_bytes({"invoice_001.zip": first, "invoice_002.zip": second})

    with pytest.raises(UnsafeArchiveError, match="recursive file count"):
        extract_invoice_archives(batch, tmp_path)


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
