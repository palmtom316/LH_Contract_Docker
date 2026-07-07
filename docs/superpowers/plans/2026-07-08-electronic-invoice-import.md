# Electronic Invoice Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an electronic invoice import workbench that parses nested invoice zip packages, detects duplicates, recommends upstream/downstream contract matches, lets operators manually split amounts, and confirms allocations into existing formal invoice tables.

**Architecture:** Add an independent import module around new batch, item, allocation, and match-candidate tables. XML parsing and contract matching run before posting; posting happens only when an operator confirms allocations. Existing upstream and downstream invoice tables remain the source used by contract detail pages and reports.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL, MinIO, Vue 3, Element Plus, Vitest, Pytest.

## Global Constraints

- First release supports upstream and downstream contract invoices only.
- First release does not support non-contract expenses.
- First release uses invoice XML as the structured source of truth.
- First release does not implement OCR.
- First release does not automatically split invoice amounts across contracts.
- Operators must confirm allocations before formal invoice records are created.
- One fixed company identity is configured by `COMPANY_NAME` and `COMPANY_TAX_NO`.
- A source invoice may be split across multiple contract allocations.
- Allocation total must be greater than zero and must not exceed invoice total amount.
- Imported source files are stored under MinIO prefix `invoices/imports/`.

---

## File Structure

- Create `backend/app/models/invoice_import.py`: SQLAlchemy models for batches, items, allocations, and candidates.
- Modify `backend/app/models/contract_upstream.py`: add party tax number fields and import trace fields on upstream invoices.
- Modify `backend/app/models/contract_downstream.py`: add party tax number fields and import trace fields on downstream invoices.
- Modify `backend/app/models/__init__.py`: import invoice import models.
- Create Alembic migration under `backend/alembic/versions/`: create import tables and add nullable trace/tax columns.
- Create `backend/app/schemas/invoice_import.py`: API request/response schemas.
- Create `backend/app/services/invoice_import/archive.py`: safe archive inspection and extraction helpers.
- Create `backend/app/services/invoice_import/parser.py`: XML parsing and normalization.
- Create `backend/app/services/invoice_import/matching.py`: contract candidate scoring.
- Create `backend/app/services/invoice_import/posting.py`: transactional confirmation into formal invoice tables.
- Create `backend/app/services/invoice_import/service.py`: batch orchestration.
- Create `backend/app/routers/invoice_imports.py`: import workbench endpoints.
- Modify `backend/app/main.py`: register invoice import router.
- Modify `backend/app/config.py`: add company identity and import limits.
- Create backend tests under `backend/tests/test_invoice_import_*.py`.
- Create `frontend/src/api/invoiceImport.js`: frontend API wrapper.
- Modify `frontend/src/router/index.js`: add invoice import route.
- Create `frontend/src/views/invoices/InvoiceImportWorkbench.vue`: upload, batch, item, and allocation workbench.
- Create `frontend/src/views/invoices/__tests__/InvoiceImportWorkbench.spec.js`: frontend behavior tests.
- Modify deployment docs or `.env.example`: document `COMPANY_NAME` and `COMPANY_TAX_NO`.

---

### Task 1: Database Models And Migration

**Files:**
- Create: `backend/app/models/invoice_import.py`
- Modify: `backend/app/models/contract_upstream.py`
- Modify: `backend/app/models/contract_downstream.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/20260708_add_invoice_imports.py`
- Test: `backend/tests/test_invoice_import_models.py`

**Interfaces:**
- Produces: `InvoiceImportBatch`, `InvoiceImportItem`, `InvoiceImportAllocation`, `InvoiceImportMatchCandidate`.
- Produces: nullable trace columns `source_import_item_id` and `source_import_allocation_id` on formal invoice models.

- [ ] **Step 1: Write failing model registration test**

Create `backend/tests/test_invoice_import_models.py`:

```python
from app.database import Base


def test_invoice_import_tables_are_registered():
    table_names = set(Base.metadata.tables.keys())

    assert "invoice_import_batches" in table_names
    assert "invoice_import_items" in table_names
    assert "invoice_import_allocations" in table_names
    assert "invoice_import_match_candidates" in table_names


def test_formal_invoice_trace_columns_are_registered():
    upstream = Base.metadata.tables["finance_upstream_invoices"]
    downstream = Base.metadata.tables["finance_downstream_invoices"]

    assert "source_import_item_id" in upstream.c
    assert "source_import_allocation_id" in upstream.c
    assert "source_import_item_id" in downstream.c
    assert "source_import_allocation_id" in downstream.c
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_invoice_import_models.py -v
```

Expected: fails because import tables and trace columns are not registered.

- [ ] **Step 3: Add invoice import models**

Create `backend/app/models/invoice_import.py`:

```python
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InvoiceImportBatch(Base):
    __tablename__ = "invoice_import_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_code = Column(String(50), unique=True, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    archive_file_path = Column(String(500), nullable=True)
    archive_file_key = Column(String(500), nullable=True)
    storage_provider = Column(String(50), default="minio")
    status = Column(String(50), nullable=False, default="uploaded", index=True)
    total_items = Column(Integer, nullable=False, default=0)
    parsed_items = Column(Integer, nullable=False, default=0)
    duplicate_items = Column(Integer, nullable=False, default=0)
    error_items = Column(Integer, nullable=False, default=0)
    confirmed_items = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    items = relationship("InvoiceImportItem", back_populates="batch", cascade="all, delete-orphan")


class InvoiceImportItem(Base):
    __tablename__ = "invoice_import_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("invoice_import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    source_archive_name = Column(String(255), nullable=False)
    invoice_number = Column(String(100), nullable=True, index=True)
    invoice_code = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=True, index=True)
    seller_name = Column(String(200), nullable=True, index=True)
    seller_tax_no = Column(String(50), nullable=True, index=True)
    buyer_name = Column(String(200), nullable=True, index=True)
    buyer_tax_no = Column(String(50), nullable=True, index=True)
    amount_without_tax = Column(Numeric(15, 2), nullable=True)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=True)
    invoice_type = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    dedupe_key = Column(String(255), nullable=True, index=True)
    duplicate_of_item_id = Column(Integer, ForeignKey("invoice_import_items.id"), nullable=True)
    direction = Column(String(50), nullable=False, default="unknown", index=True)
    parse_status = Column(String(50), nullable=False, default="needs_review", index=True)
    match_status = Column(String(50), nullable=False, default="not_matched", index=True)
    confirmation_status = Column(String(50), nullable=False, default="draft", index=True)
    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_key = Column(String(500), nullable=True)
    ofd_file_path = Column(String(500), nullable=True)
    ofd_file_key = Column(String(500), nullable=True)
    xml_file_path = Column(String(500), nullable=True)
    xml_file_key = Column(String(500), nullable=True)
    raw_xml = Column(Text, nullable=True)
    parsed_payload = Column(JSONB, nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    batch = relationship("InvoiceImportBatch", back_populates="items")
    allocations = relationship("InvoiceImportAllocation", back_populates="item", cascade="all, delete-orphan")
    candidates = relationship("InvoiceImportMatchCandidate", back_populates="item", cascade="all, delete-orphan")
    duplicate_of = relationship("InvoiceImportItem", remote_side=[id])


class InvoiceImportAllocation(Base):
    __tablename__ = "invoice_import_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("invoice_import_items.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(50), nullable=False, index=True)
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="RESTRICT"), nullable=True, index=True)
    downstream_contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="RESTRICT"), nullable=True, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    description = Column(String(300), nullable=True)
    status = Column(String(50), nullable=False, default="draft", index=True)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    formal_invoice_id = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    item = relationship("InvoiceImportItem", back_populates="allocations")


class InvoiceImportMatchCandidate(Base):
    __tablename__ = "invoice_import_match_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("invoice_import_items.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(50), nullable=False, index=True)
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="CASCADE"), nullable=True, index=True)
    downstream_contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="CASCADE"), nullable=True, index=True)
    score = Column(Integer, nullable=False, default=0)
    matched_signals = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    item = relationship("InvoiceImportItem", back_populates="candidates")
```

- [ ] **Step 4: Add model imports and trace columns**

Modify `backend/app/models/__init__.py` to import:

```python
from app.models.invoice_import import (
    InvoiceImportAllocation,
    InvoiceImportBatch,
    InvoiceImportItem,
    InvoiceImportMatchCandidate,
)
```

In `backend/app/models/contract_upstream.py`, add to `ContractUpstream`:

```python
party_a_tax_no = Column(String(50), nullable=True, index=True)
party_b_tax_no = Column(String(50), nullable=True, index=True)
```

In `FinanceUpstreamInvoice`, add:

```python
source_import_item_id = Column(Integer, ForeignKey("invoice_import_items.id"), nullable=True, index=True)
source_import_allocation_id = Column(Integer, ForeignKey("invoice_import_allocations.id"), nullable=True, index=True)
```

In `backend/app/models/contract_downstream.py`, add to `ContractDownstream`:

```python
party_a_tax_no = Column(String(50), nullable=True, index=True)
party_b_tax_no = Column(String(50), nullable=True, index=True)
```

In `FinanceDownstreamInvoice`, add:

```python
source_import_item_id = Column(Integer, ForeignKey("invoice_import_items.id"), nullable=True, index=True)
source_import_allocation_id = Column(Integer, ForeignKey("invoice_import_allocations.id"), nullable=True, index=True)
```

- [ ] **Step 5: Create Alembic migration**

Create `backend/alembic/versions/20260708_add_invoice_imports.py` with table creation, nullable tax columns, and nullable trace columns. Include a PostgreSQL partial unique index:

```python
op.create_index(
    "uq_invoice_import_items_active_dedupe",
    "invoice_import_items",
    ["dedupe_key"],
    unique=True,
    postgresql_where=sa.text("duplicate_of_item_id IS NULL AND dedupe_key IS NOT NULL"),
)
```

- [ ] **Step 6: Run tests and migration check**

Run:

```bash
cd backend && pytest tests/test_invoice_import_models.py -v
cd backend && alembic upgrade head
```

Expected: model test passes and migration applies cleanly.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models backend/alembic/versions/20260708_add_invoice_imports.py backend/tests/test_invoice_import_models.py
git commit -m "feat: add invoice import data model"
```

---

### Task 2: Configuration And Schemas

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/app/schemas/invoice_import.py`
- Modify: `.env.example`
- Test: `backend/tests/test_invoice_import_config_schema.py`

**Interfaces:**
- Produces config fields: `COMPANY_NAME`, `COMPANY_TAX_NO`, `INVOICE_IMPORT_MAX_ARCHIVE_SIZE`, `INVOICE_IMPORT_MAX_FILE_SIZE`.
- Produces Pydantic schemas consumed by router and frontend.

- [ ] **Step 1: Write failing config and schema tests**

Create `backend/tests/test_invoice_import_config_schema.py`:

```python
from decimal import Decimal

from app.schemas.invoice_import import AllocationCreate, InvoiceDirection


def test_allocation_create_requires_one_target_contract():
    allocation = AllocationCreate(direction=InvoiceDirection.UPSTREAM, upstream_contract_id=1, amount=Decimal("100.00"))

    assert allocation.direction == InvoiceDirection.UPSTREAM
    assert allocation.upstream_contract_id == 1
    assert allocation.downstream_contract_id is None


def test_invoice_direction_values_are_stable():
    assert InvoiceDirection.UPSTREAM.value == "upstream"
    assert InvoiceDirection.DOWNSTREAM.value == "downstream"
    assert InvoiceDirection.UNKNOWN.value == "unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_invoice_import_config_schema.py -v
```

Expected: fails because `app.schemas.invoice_import` does not exist.

- [ ] **Step 3: Add config fields**

In `backend/app/config.py`, add:

```python
COMPANY_NAME: str = os.getenv("COMPANY_NAME", "")
COMPANY_TAX_NO: str = os.getenv("COMPANY_TAX_NO", "")
INVOICE_IMPORT_MAX_ARCHIVE_SIZE: int = int(os.getenv("INVOICE_IMPORT_MAX_ARCHIVE_SIZE", str(200 * 1024 * 1024)))
INVOICE_IMPORT_MAX_FILE_SIZE: int = int(os.getenv("INVOICE_IMPORT_MAX_FILE_SIZE", str(50 * 1024 * 1024)))
```

In production validation, require `COMPANY_TAX_NO` when invoice import is enabled by adding:

```python
if not self.DEBUG and not self.COMPANY_TAX_NO:
    raise ValueError("COMPANY_TAX_NO 环境变量在生产环境中必须设置，用于电子发票上下游方向判断")
```

- [ ] **Step 4: Add invoice import schemas**

Create `backend/app/schemas/invoice_import.py`:

```python
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class InvoiceDirection(str, Enum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    UNKNOWN = "unknown"


class BatchStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class AllocationStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class AllocationCreate(BaseModel):
    direction: InvoiceDirection
    upstream_contract_id: Optional[int] = Field(None, gt=0)
    downstream_contract_id: Optional[int] = Field(None, gt=0)
    amount: Decimal = Field(..., gt=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=300)

    @model_validator(mode="after")
    def validate_target_contract(self) -> "AllocationCreate":
        if self.direction == InvoiceDirection.UPSTREAM:
            if not self.upstream_contract_id or self.downstream_contract_id:
                raise ValueError("上游分摊必须且只能选择上游合同")
        if self.direction == InvoiceDirection.DOWNSTREAM:
            if not self.downstream_contract_id or self.upstream_contract_id:
                raise ValueError("下游分摊必须且只能选择下游合同")
        return self


class AllocationUpdate(BaseModel):
    upstream_contract_id: Optional[int] = Field(None, gt=0)
    downstream_contract_id: Optional[int] = Field(None, gt=0)
    amount: Optional[Decimal] = Field(None, gt=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=300)


class MatchCandidateResponse(BaseModel):
    id: int
    direction: InvoiceDirection
    upstream_contract_id: Optional[int] = None
    downstream_contract_id: Optional[int] = None
    score: int
    matched_signals: Dict[str, Any]

    class Config:
        from_attributes = True


class AllocationResponse(BaseModel):
    id: int
    item_id: int
    direction: InvoiceDirection
    upstream_contract_id: Optional[int] = None
    downstream_contract_id: Optional[int] = None
    amount: Decimal
    tax_amount: Optional[Decimal] = None
    description: Optional[str] = None
    status: AllocationStatus
    formal_invoice_id: Optional[int] = None
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImportItemResponse(BaseModel):
    id: int
    batch_id: int
    source_archive_name: str
    invoice_number: Optional[str] = None
    invoice_code: Optional[str] = None
    invoice_date: Optional[date] = None
    seller_name: Optional[str] = None
    seller_tax_no: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_tax_no: Optional[str] = None
    amount_without_tax: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    invoice_type: Optional[str] = None
    remarks: Optional[str] = None
    direction: InvoiceDirection
    parse_status: str
    match_status: str
    confirmation_status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    allocations: List[AllocationResponse] = []
    candidates: List[MatchCandidateResponse] = []

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    batch_code: str
    original_filename: str
    status: BatchStatus
    total_items: int
    parsed_items: int
    duplicate_items: int
    error_items: int
    confirmed_items: int
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfirmItemRequest(BaseModel):
    override_duplicate: bool = False


class IgnoreItemRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=300)
```

- [ ] **Step 5: Document env vars**

Append to `.env.example`:

```dotenv
# Electronic invoice import
COMPANY_NAME=示例公司名称
COMPANY_TAX_NO=913XXXXXXXXXXXXXXX
INVOICE_IMPORT_MAX_ARCHIVE_SIZE=209715200
INVOICE_IMPORT_MAX_FILE_SIZE=52428800
```

- [ ] **Step 6: Run tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_config_schema.py -v
```

Expected: schema tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/config.py backend/app/schemas/invoice_import.py backend/tests/test_invoice_import_config_schema.py .env.example
git commit -m "feat: add invoice import configuration and schemas"
```

---

### Task 3: Safe Archive Extraction And XML Parser

**Files:**
- Create: `backend/app/services/invoice_import/__init__.py`
- Create: `backend/app/services/invoice_import/archive.py`
- Create: `backend/app/services/invoice_import/parser.py`
- Test: `backend/tests/test_invoice_import_archive_parser.py`

**Interfaces:**
- Produces: `extract_invoice_archives(batch_zip: BinaryIO, work_dir: Path) -> list[ExtractedInvoicePackage]`.
- Produces: `parse_invoice_xml(xml_bytes: bytes) -> ParsedInvoice`.
- Consumes: config import size limits from Task 2.

- [ ] **Step 1: Write failing archive and parser tests**

Create `backend/tests/test_invoice_import_archive_parser.py`:

```python
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
    xml = b"""
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
    """

    parsed = parse_invoice_xml(xml)

    assert parsed.invoice_number == "INV-001"
    assert parsed.invoice_date.isoformat() == "2026-07-08"
    assert parsed.seller_tax_no == "SELLER123"
    assert parsed.buyer_tax_no == "BUYER123"
    assert parsed.total_amount == Decimal("106.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_invoice_import_archive_parser.py -v
```

Expected: fails because archive and parser modules do not exist.

- [ ] **Step 3: Implement archive extraction**

Create `backend/app/services/invoice_import/archive.py` with:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional
import zipfile


class UnsafeArchiveError(ValueError):
    pass


@dataclass(frozen=True)
class ExtractedInvoicePackage:
    source_archive_name: str
    package_dir: Path
    xml_path: Path
    pdf_path: Optional[Path]
    ofd_path: Optional[Path]


def _assert_safe_member_name(name: str) -> None:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchiveError(f"Unsafe archive path: {name}")


def _extract_nested_invoice(source_archive_name: str, nested_bytes: bytes, target_dir: Path) -> ExtractedInvoicePackage:
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_paths: list[Path] = []
    pdf_path: Optional[Path] = None
    ofd_path: Optional[Path] = None

    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
        for info in nested.infolist():
            _assert_safe_member_name(info.filename)
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix == ".zip":
                raise UnsafeArchiveError("Nested invoice archive contains another zip")
            output_path = target_dir / Path(info.filename).name
            output_path.write_bytes(nested.read(info))
            if suffix == ".xml":
                xml_paths.append(output_path)
            elif suffix == ".pdf":
                pdf_path = output_path
            elif suffix == ".ofd":
                ofd_path = output_path

    if len(xml_paths) != 1:
        raise UnsafeArchiveError(f"Invoice archive must contain exactly one XML file: {source_archive_name}")

    return ExtractedInvoicePackage(
        source_archive_name=source_archive_name,
        package_dir=target_dir,
        xml_path=xml_paths[0],
        pdf_path=pdf_path,
        ofd_path=ofd_path,
    )
```

Add `import io` at the top of the file. Then implement `extract_invoice_archives`:

```python
def extract_invoice_archives(batch_zip: BinaryIO, work_dir: Path) -> list[ExtractedInvoicePackage]:
    packages: list[ExtractedInvoicePackage] = []
    with zipfile.ZipFile(batch_zip) as batch:
        for index, info in enumerate(batch.infolist(), start=1):
            _assert_safe_member_name(info.filename)
            if info.is_dir():
                continue
            if Path(info.filename).suffix.lower() != ".zip":
                raise UnsafeArchiveError("Top-level archive may contain invoice zip files only")
            nested_bytes = batch.read(info)
            package_dir = work_dir / f"invoice_{index:04d}"
            packages.append(_extract_nested_invoice(info.filename, nested_bytes, package_dir))
    return packages
```

- [ ] **Step 4: Implement XML parser**

Create `backend/app/services/invoice_import/parser.py`:

```python
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET


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
    for alias in aliases:
        node = root.find(f".//{alias}")
        if node is not None and node.text and node.text.strip():
            return node.text.strip()
    return None


def _to_decimal(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None
    return Decimal(value.replace(",", "").strip()).quantize(Decimal("0.01"))


def _to_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    normalized = value.strip().replace("/", "-")
    return date.fromisoformat(normalized[:10])


def parse_invoice_xml(xml_bytes: bytes) -> ParsedInvoice:
    root = ET.fromstring(xml_bytes)
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
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_archive_parser.py -v
```

Expected: archive and parser tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/invoice_import backend/tests/test_invoice_import_archive_parser.py
git commit -m "feat: parse electronic invoice archives"
```

---

### Task 4: Direction, Dedupe, And Contract Matching

**Files:**
- Create: `backend/app/services/invoice_import/matching.py`
- Test: `backend/tests/test_invoice_import_matching.py`

**Interfaces:**
- Produces: `build_dedupe_key(parsed: ParsedInvoice) -> str`.
- Produces: `detect_direction(parsed: ParsedInvoice, company_tax_no: str) -> str`.
- Produces: `InvoiceMatchService.find_candidates(item: InvoiceImportItem) -> list[InvoiceImportMatchCandidate]`.

- [ ] **Step 1: Write failing matching tests**

Create `backend/tests/test_invoice_import_matching.py`:

```python
from datetime import date
from decimal import Decimal

from app.services.invoice_import.matching import build_dedupe_key, detect_direction
from app.services.invoice_import.parser import ParsedInvoice


def _parsed(**overrides):
    data = {
        "invoice_number": "INV-001",
        "invoice_code": None,
        "invoice_date": date(2026, 7, 8),
        "seller_name": "我方公司",
        "seller_tax_no": "OUR-TAX",
        "buyer_name": "客户A",
        "buyer_tax_no": "BUYER-TAX",
        "amount_without_tax": Decimal("100.00"),
        "tax_amount": Decimal("6.00"),
        "total_amount": Decimal("106.00"),
        "invoice_type": "数电票",
        "remarks": "HT-001",
        "payload": {},
    }
    data.update(overrides)
    return ParsedInvoice(**data)


def test_detects_upstream_direction_when_seller_is_company():
    assert detect_direction(_parsed(), "OUR-TAX") == "upstream"


def test_detects_downstream_direction_when_buyer_is_company():
    parsed = _parsed(seller_tax_no="SUPPLIER-TAX", buyer_tax_no="OUR-TAX")
    assert detect_direction(parsed, "OUR-TAX") == "downstream"


def test_build_dedupe_key_is_stable():
    key = build_dedupe_key(_parsed())
    assert key == "INV-001|OUR-TAX|BUYER-TAX|2026-07-08|106.00"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_invoice_import_matching.py -v
```

Expected: fails because matching module does not exist.

- [ ] **Step 3: Implement direction and dedupe helpers**

Create `backend/app/services/invoice_import/matching.py`:

```python
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
```

- [ ] **Step 4: Implement candidate scoring service**

Append to `matching.py`:

```python
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
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_matching.py -v
```

Expected: direction and dedupe tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/invoice_import/matching.py backend/tests/test_invoice_import_matching.py
git commit -m "feat: match imported invoices to contracts"
```

---

### Task 5: Posting Service

**Files:**
- Create: `backend/app/services/invoice_import/posting.py`
- Test: `backend/tests/test_invoice_import_posting.py`

**Interfaces:**
- Consumes: `InvoiceImportItem` and `InvoiceImportAllocation`.
- Produces: `InvoicePostingService.confirm_item(item_id: int, user: User, override_duplicate: bool = False) -> InvoiceImportItem`.

- [ ] **Step 1: Write failing posting validation test**

Create `backend/tests/test_invoice_import_posting.py`:

```python
from decimal import Decimal

import pytest

from app.core.errors import ValidationError
from app.services.invoice_import.posting import validate_allocation_total


def test_rejects_allocation_total_above_invoice_total():
    with pytest.raises(ValidationError):
        validate_allocation_total(Decimal("100.00"), [Decimal("60.00"), Decimal("50.00")])


def test_accepts_allocation_total_equal_invoice_total():
    validate_allocation_total(Decimal("100.00"), [Decimal("60.00"), Decimal("40.00")])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_invoice_import_posting.py -v
```

Expected: fails because posting module does not exist.

- [ ] **Step 3: Implement posting validation**

Create `backend/app/services/invoice_import/posting.py`:

```python
from decimal import Decimal
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ResourceNotFoundError, ValidationError
from app.models.contract_downstream import FinanceDownstreamInvoice
from app.models.contract_upstream import FinanceUpstreamInvoice
from app.models.invoice_import import InvoiceImportAllocation, InvoiceImportItem
from app.models.user import User


def validate_allocation_total(invoice_total: Decimal, allocation_amounts: Iterable[Decimal]) -> None:
    total = sum(allocation_amounts, Decimal("0.00"))
    if total <= Decimal("0.00"):
        raise ValidationError(message="分摊金额必须大于 0", field_errors={"amount": "分摊金额必须大于 0"})
    if total > invoice_total:
        raise ValidationError(message="分摊金额超过发票价税合计", field_errors={"amount": "分摊金额超过发票价税合计"})
```

- [ ] **Step 4: Implement confirmation service**

Append to `posting.py`:

```python
class InvoicePostingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def confirm_item(self, item_id: int, user: User, override_duplicate: bool = False) -> InvoiceImportItem:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.allocations))
            .where(InvoiceImportItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ResourceNotFoundError(resource_type="导入发票", resource_id=item_id)
        if item.confirmation_status == "confirmed":
            return item
        if item.duplicate_of_item_id and not override_duplicate:
            raise ValidationError(message="重复发票不能直接确认", field_errors={"invoice_number": "请核对重复发票"})

        draft_allocations = [a for a in item.allocations if a.status == "draft"]
        validate_allocation_total(item.total_amount, [a.amount for a in draft_allocations])

        for allocation in draft_allocations:
            if allocation.direction == "upstream":
                formal = FinanceUpstreamInvoice(
                    contract_id=allocation.upstream_contract_id,
                    invoice_number=item.invoice_number,
                    invoice_date=item.invoice_date,
                    amount=allocation.amount,
                    tax_amount=allocation.tax_amount,
                    invoice_type=item.invoice_type,
                    description=allocation.description or item.remarks,
                    file_path=item.pdf_file_path or item.ofd_file_path,
                    file_key=item.pdf_file_key or item.ofd_file_key,
                    storage_provider="minio",
                    source_import_item_id=item.id,
                    source_import_allocation_id=allocation.id,
                    created_by=user.id,
                    updated_by=user.id,
                )
            else:
                formal = FinanceDownstreamInvoice(
                    contract_id=allocation.downstream_contract_id,
                    invoice_number=item.invoice_number,
                    invoice_date=item.invoice_date,
                    amount=allocation.amount,
                    tax_amount=allocation.tax_amount,
                    invoice_type=item.invoice_type,
                    supplier_name=item.seller_name,
                    description=allocation.description or item.remarks,
                    file_path=item.pdf_file_path or item.ofd_file_path,
                    file_key=item.pdf_file_key or item.ofd_file_key,
                    storage_provider="minio",
                    source_import_item_id=item.id,
                    source_import_allocation_id=allocation.id,
                    created_by=user.id,
                    updated_by=user.id,
                )
            self.db.add(formal)
            await self.db.flush()
            allocation.status = "confirmed"
            allocation.confirmed_by = user.id
            allocation.formal_invoice_id = formal.id

        item.confirmation_status = "confirmed"
        await self.db.commit()
        await self.db.refresh(item)
        return item
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_posting.py -v
```

Expected: posting validation tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/invoice_import/posting.py backend/tests/test_invoice_import_posting.py
git commit -m "feat: post confirmed invoice allocations"
```

---

### Task 6: Batch Service And API Router

**Files:**
- Create: `backend/app/services/invoice_import/service.py`
- Create: `backend/app/routers/invoice_imports.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_invoice_import_api.py`

**Interfaces:**
- Produces API prefix `/api/v1/invoice-imports`.
- Consumes schemas from Task 2 and services from Tasks 3-5.

- [ ] **Step 1: Write failing router registration test**

Create `backend/tests/test_invoice_import_api.py`:

```python
from app.main import app


def test_invoice_import_router_is_registered():
    paths = {route.path for route in app.routes}

    assert "/api/v1/invoice-imports/batches" in paths
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_invoice_import_api.py -v
```

Expected: fails because router is not registered.

- [ ] **Step 3: Implement service skeleton**

Create `backend/app/services/invoice_import/service.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ResourceNotFoundError
from app.models.invoice_import import InvoiceImportAllocation, InvoiceImportBatch, InvoiceImportItem
from app.models.user import User
from app.schemas.invoice_import import AllocationCreate, AllocationUpdate


class InvoiceImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_batches(self) -> list[InvoiceImportBatch]:
        result = await self.db.execute(select(InvoiceImportBatch).order_by(InvoiceImportBatch.created_at.desc()))
        return list(result.scalars().all())

    async def get_batch(self, batch_id: int) -> InvoiceImportBatch:
        result = await self.db.execute(select(InvoiceImportBatch).where(InvoiceImportBatch.id == batch_id))
        batch = result.scalar_one_or_none()
        if not batch:
            raise ResourceNotFoundError(resource_type="发票导入批次", resource_id=batch_id)
        return batch

    async def list_items(self, batch_id: int) -> list[InvoiceImportItem]:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.allocations), selectinload(InvoiceImportItem.candidates))
            .where(InvoiceImportItem.batch_id == batch_id)
            .order_by(InvoiceImportItem.id.desc())
        )
        return list(result.scalars().all())

    async def create_allocation(self, item_id: int, allocation_in: AllocationCreate, user: User) -> InvoiceImportAllocation:
        data = allocation_in.model_dump()
        allocation = InvoiceImportAllocation(item_id=item_id, created_by=user.id, **data)
        self.db.add(allocation)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation

    async def update_allocation(self, allocation_id: int, allocation_in: AllocationUpdate) -> InvoiceImportAllocation:
        result = await self.db.execute(select(InvoiceImportAllocation).where(InvoiceImportAllocation.id == allocation_id))
        allocation = result.scalar_one_or_none()
        if not allocation:
            raise ResourceNotFoundError(resource_type="发票分摊", resource_id=allocation_id)
        for key, value in allocation_in.model_dump(exclude_unset=True).items():
            setattr(allocation, key, value)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation
```

- [ ] **Step 4: Implement router**

Create `backend/app/routers/invoice_imports.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.invoice_import import (
    AllocationCreate,
    AllocationResponse,
    AllocationUpdate,
    BatchResponse,
    ConfirmItemRequest,
    ImportItemResponse,
)
from app.services.invoice_import.posting import InvoicePostingService
from app.services.invoice_import.service import InvoiceImportService

router = APIRouter()


def get_import_service(db: AsyncSession = Depends(get_db)) -> InvoiceImportService:
    return InvoiceImportService(db)


@router.get("/batches", response_model=list[BatchResponse])
async def list_batches(
    current_user: User = Depends(require_permission(Permission.VIEW_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.list_batches()


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.get_batch(batch_id)


@router.get("/batches/{batch_id}/items", response_model=list[ImportItemResponse])
async def list_items(
    batch_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.list_items(batch_id)


@router.post("/items/{item_id}/allocations", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    item_id: int,
    allocation_in: AllocationCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.create_allocation(item_id, allocation_in, current_user)


@router.put("/allocations/{allocation_id}", response_model=AllocationResponse)
async def update_allocation(
    allocation_id: int,
    allocation_in: AllocationUpdate,
    current_user: User = Depends(require_permission(Permission.EDIT_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.update_allocation(allocation_id, allocation_in)


@router.post("/items/{item_id}/confirm", response_model=ImportItemResponse)
async def confirm_item(
    item_id: int,
    request: ConfirmItemRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    db: AsyncSession = Depends(get_db),
):
    return await InvoicePostingService(db).confirm_item(item_id, current_user, request.override_duplicate)
```

Modify `backend/app/main.py`:

```python
from app.routers import invoice_imports
app.include_router(invoice_imports.router, prefix="/api/v1/invoice-imports", tags=["Invoice Imports"])
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_api.py -v
```

Expected: router registration test passes.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/invoice_import/service.py backend/app/routers/invoice_imports.py backend/app/main.py backend/tests/test_invoice_import_api.py
git commit -m "feat: expose invoice import API"
```

---

### Task 7: Batch Upload Processing

**Files:**
- Modify: `backend/app/services/invoice_import/service.py`
- Modify: `backend/app/routers/invoice_imports.py`
- Test: `backend/tests/test_invoice_import_batch_processing.py`

**Interfaces:**
- Produces: `InvoiceImportService.create_batch_from_upload(file: UploadFile, user: User) -> InvoiceImportBatch`.
- Produces: `InvoiceImportService.process_uploaded_batch(batch_id: int) -> None`.

- [ ] **Step 1: Write failing batch processing test**

Create `backend/tests/test_invoice_import_batch_processing.py`:

```python
from datetime import date
from decimal import Decimal

from app.services.invoice_import.matching import build_dedupe_key
from app.services.invoice_import.parser import ParsedInvoice


def test_import_dedupe_key_for_realistic_invoice():
    parsed = ParsedInvoice(
        invoice_number="24572000000000123456",
        invoice_code=None,
        invoice_date=date(2026, 7, 8),
        seller_name="我方公司",
        seller_tax_no="913000000000000001",
        buyer_name="客户A",
        buyer_tax_no="913000000000000002",
        amount_without_tax=Decimal("1000.00"),
        tax_amount=Decimal("60.00"),
        total_amount=Decimal("1060.00"),
        invoice_type="电子发票",
        remarks="项目合同 HT-2026-001",
        payload={},
    )

    assert build_dedupe_key(parsed) == "24572000000000123456|913000000000000001|913000000000000002|2026-07-08|1060.00"
```

- [ ] **Step 2: Run current tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_batch_processing.py tests/test_invoice_import_archive_parser.py tests/test_invoice_import_matching.py -v
```

Expected: tests pass before wiring upload processing.

- [ ] **Step 3: Implement upload processing in service**

In `backend/app/services/invoice_import/service.py`, add methods that:

```python
async def create_batch_from_upload(self, file: UploadFile, user: User) -> InvoiceImportBatch:
    if not file.filename.lower().endswith(".zip"):
        raise ValidationError(message="文件格式错误", field_errors={"file": "只支持 zip 压缩包"})
    content = await file.read()
    if len(content) > settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE:
        raise ValidationError(message="文件过大", field_errors={"file": "发票批次压缩包超过大小限制"})
    object_key = f"invoices/imports/batches/{datetime.utcnow().strftime('%Y/%m')}/{uuid.uuid4()}.zip"
    batch = InvoiceImportBatch(
        batch_code=f"INVIMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        original_filename=file.filename,
        archive_file_path=object_key,
        archive_file_key=object_key,
        storage_provider="minio",
        status="uploaded",
        created_by=user.id,
    )
    self.db.add(batch)
    await self.db.commit()
    await self.db.refresh(batch)
    await self._put_bytes_to_minio(batch.archive_file_key, content, "application/zip")
    return batch
```

Add imports in the same file:

```python
from datetime import datetime
from pathlib import Path
import tempfile
import uuid
from fastapi import UploadFile
from app.config import settings
from app.core.errors import ValidationError
```

Implement `process_uploaded_batch` using `extract_invoice_archives`, `parse_invoice_xml`, `detect_direction`, and `build_dedupe_key`. It loads the batch zip from MinIO by `batch.archive_file_key`, writes it to a temporary file, extracts one invoice package per nested zip, and creates item rows. For each package:

- Create an `InvoiceImportItem`.
- Store parse errors as item-level errors.
- Insert match candidates returned by `InvoiceMatchService`.
- Update batch counters.
- Mark batch `completed` or `completed_with_errors`.

- [ ] **Step 4: Add upload endpoint**

In `backend/app/routers/invoice_imports.py`, add:

```python
@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_batch(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    batch = await service.create_batch_from_upload(file, current_user)
    background_tasks.add_task(service.process_uploaded_batch, batch.id)
    return batch
```

Add imports:

```python
from fastapi import BackgroundTasks, UploadFile
```

- [ ] **Step 5: Run focused backend tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_*.py -v
```

Expected: all invoice import backend tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/invoice_import/service.py backend/app/routers/invoice_imports.py backend/tests/test_invoice_import_batch_processing.py
git commit -m "feat: process invoice import batches"
```

---

### Task 8: Frontend API And Workbench Page

**Files:**
- Create: `frontend/src/api/invoiceImport.js`
- Create: `frontend/src/views/invoices/InvoiceImportWorkbench.vue`
- Create: `frontend/src/views/invoices/__tests__/InvoiceImportWorkbench.spec.js`
- Modify: `frontend/src/router/index.js`

**Interfaces:**
- Consumes: `/api/v1/invoice-imports/batches`, `/batches/{id}/items`, `/items/{id}/allocations`, `/items/{id}/confirm`.
- Produces: route `/invoice-imports`.

- [ ] **Step 1: Write failing frontend test**

Create `frontend/src/views/invoices/__tests__/InvoiceImportWorkbench.spec.js`:

```javascript
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import InvoiceImportWorkbench from '../InvoiceImportWorkbench.vue'

vi.mock('@/api/invoiceImport', () => ({
  listBatches: vi.fn().mockResolvedValue([
    {
      id: 1,
      batch_code: 'INVIMP-202607080001',
      original_filename: 'batch.zip',
      status: 'completed',
      total_items: 2,
      parsed_items: 2,
      duplicate_items: 0,
      error_items: 0,
      confirmed_items: 0,
    },
  ]),
  listBatchItems: vi.fn().mockResolvedValue([]),
}))

describe('InvoiceImportWorkbench', () => {
  it('renders batch list title and loaded batch code', async () => {
    const wrapper = mount(InvoiceImportWorkbench)
    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain('电子发票导入')
    expect(wrapper.text()).toContain('INVIMP-202607080001')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npm run test -- InvoiceImportWorkbench.spec.js
```

Expected: fails because API and view do not exist.

- [ ] **Step 3: Add frontend API wrapper**

Create `frontend/src/api/invoiceImport.js`:

```javascript
import request from '@/utils/request'

export function uploadBatch(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/invoice-imports/batches',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function listBatches() {
  return request({ url: '/invoice-imports/batches', method: 'get' })
}

export function listBatchItems(batchId) {
  return request({ url: `/invoice-imports/batches/${batchId}/items`, method: 'get' })
}

export function createAllocation(itemId, data) {
  return request({ url: `/invoice-imports/items/${itemId}/allocations`, method: 'post', data })
}

export function updateAllocation(allocationId, data) {
  return request({ url: `/invoice-imports/allocations/${allocationId}`, method: 'put', data })
}

export function confirmItem(itemId, data = { override_duplicate: false }) {
  return request({ url: `/invoice-imports/items/${itemId}/confirm`, method: 'post', data })
}
```

- [ ] **Step 4: Add workbench page**

Create `frontend/src/views/invoices/InvoiceImportWorkbench.vue` with:

```vue
<template>
  <div class="invoice-import-workbench">
    <AppPageHeader title="电子发票导入" subtitle="上传发票压缩包，解析后确认挂账" />
    <AppWorkspacePanel>
      <template #header>
        <div class="workbench-toolbar">
          <el-upload :auto-upload="false" :show-file-list="false" accept=".zip" :on-change="handleFileSelected">
            <el-button type="primary">上传压缩包</el-button>
          </el-upload>
          <el-button @click="loadBatches">刷新</el-button>
        </div>
      </template>

      <el-table :data="batches" border>
        <el-table-column prop="batch_code" label="批次号" width="180" />
        <el-table-column prop="original_filename" label="文件名" min-width="180" />
        <el-table-column prop="status" label="状态" width="140" />
        <el-table-column prop="total_items" label="总数" width="80" />
        <el-table-column prop="parsed_items" label="已解析" width="90" />
        <el-table-column prop="duplicate_items" label="重复" width="80" />
        <el-table-column prop="error_items" label="异常" width="80" />
        <el-table-column prop="confirmed_items" label="已确认" width="90" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="selectBatch(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import { listBatches, uploadBatch } from '@/api/invoiceImport'

const batches = ref([])
const selectedBatch = ref(null)

async function loadBatches() {
  batches.value = await listBatches()
}

async function handleFileSelected(file) {
  await uploadBatch(file.raw)
  ElMessage.success('发票批次已上传，系统开始解析')
  await loadBatches()
}

function selectBatch(row) {
  selectedBatch.value = row
}

onMounted(loadBatches)
</script>
```

- [ ] **Step 5: Add route**

Modify `frontend/src/router/index.js` under the main layout children:

```javascript
{
  path: 'invoice-imports',
  name: 'InvoiceImports',
  component: () => import('@/views/invoices/InvoiceImportWorkbench.vue'),
  meta: { title: '电子发票导入', icon: 'DocumentAdd' }
}
```

- [ ] **Step 6: Run frontend test**

Run:

```bash
cd frontend && npm run test -- InvoiceImportWorkbench.spec.js
```

Expected: workbench test passes.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/invoiceImport.js frontend/src/views/invoices frontend/src/router/index.js
git commit -m "feat: add invoice import workbench"
```

---

### Task 9: Workbench Allocation And Confirmation UI

**Files:**
- Modify: `frontend/src/views/invoices/InvoiceImportWorkbench.vue`
- Test: `frontend/src/views/invoices/__tests__/InvoiceImportWorkbench.spec.js`

**Interfaces:**
- Consumes: `listBatchItems`, `createAllocation`, `updateAllocation`, `confirmItem`.
- Produces: UI for candidate review, manual allocation, and confirmation.

- [ ] **Step 1: Extend frontend test for item states**

Append to `InvoiceImportWorkbench.spec.js`:

```javascript
it('shows item states after selecting a batch', async () => {
  const api = await import('@/api/invoiceImport')
  api.listBatchItems.mockResolvedValueOnce([
    {
      id: 10,
      invoice_number: 'INV-001',
      seller_name: '我方公司',
      buyer_name: '客户A',
      total_amount: '106.00',
      direction: 'upstream',
      parse_status: 'parsed',
      match_status: 'multiple_candidates',
      confirmation_status: 'draft',
      allocations: [],
      candidates: [],
    },
  ])

  const wrapper = mount(InvoiceImportWorkbench)
  await Promise.resolve()
  await Promise.resolve()
  await wrapper.find('button').trigger('click')
  await Promise.resolve()

  expect(wrapper.text()).toContain('INV-001')
  expect(wrapper.text()).toContain('upstream')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npm run test -- InvoiceImportWorkbench.spec.js
```

Expected: fails because item table is not implemented.

- [ ] **Step 3: Add item table and detail drawer**

Extend `InvoiceImportWorkbench.vue` with:

```vue
<el-drawer v-model="itemDrawerVisible" size="60%" title="发票识别明细">
  <el-table :data="items" border>
    <el-table-column prop="invoice_number" label="发票号" width="170" />
    <el-table-column prop="direction" label="方向" width="100" />
    <el-table-column prop="seller_name" label="销售方" min-width="180" />
    <el-table-column prop="buyer_name" label="购买方" min-width="180" />
    <el-table-column prop="total_amount" label="价税合计" width="120" align="right" />
    <el-table-column prop="match_status" label="匹配" width="130" />
    <el-table-column prop="confirmation_status" label="确认" width="120" />
    <el-table-column label="操作" width="160">
      <template #default="{ row }">
        <el-button link type="primary" @click="openAllocation(row)">分摊</el-button>
        <el-button link type="success" @click="handleConfirm(row)">确认</el-button>
      </template>
    </el-table-column>
  </el-table>
</el-drawer>
```

Add script state:

```javascript
import { listBatchItems, confirmItem } from '@/api/invoiceImport'

const items = ref([])
const itemDrawerVisible = ref(false)

async function selectBatch(row) {
  selectedBatch.value = row
  items.value = await listBatchItems(row.id)
  itemDrawerVisible.value = true
}

function openAllocation(row) {
  selectedItem.value = row
  allocationDialogVisible.value = true
}

async function handleConfirm(row) {
  await confirmItem(row.id)
  ElMessage.success('已确认挂账')
  items.value = await listBatchItems(selectedBatch.value.id)
}
```

- [ ] **Step 4: Add allocation dialog**

Add a dialog with fields:

```vue
<el-dialog v-model="allocationDialogVisible" title="新增分摊" width="520px">
  <el-form label-width="100px">
    <el-form-item label="方向">
      <el-input v-model="allocationForm.direction" disabled />
    </el-form-item>
    <el-form-item label="合同ID">
      <el-input-number v-model="allocationForm.contract_id" :min="1" style="width: 100%" />
    </el-form-item>
    <el-form-item label="分摊金额">
      <el-input-number v-model="allocationForm.amount" :min="0.01" :precision="2" style="width: 100%" />
    </el-form-item>
    <el-form-item label="说明">
      <el-input v-model="allocationForm.description" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="allocationDialogVisible = false">取消</el-button>
    <el-button type="primary" @click="saveAllocation">保存</el-button>
  </template>
</el-dialog>
```

Map the contract ID by direction before calling `createAllocation`.

- [ ] **Step 5: Run frontend tests**

Run:

```bash
cd frontend && npm run test -- InvoiceImportWorkbench.spec.js
```

Expected: workbench tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/invoices/InvoiceImportWorkbench.vue frontend/src/views/invoices/__tests__/InvoiceImportWorkbench.spec.js
git commit -m "feat: confirm invoice import allocations"
```

---

### Task 10: End-To-End Verification And Release Docs

**Files:**
- Modify: `docs/API_DOCUMENTATION.md`
- Modify: `README_CN.md`
- Modify: `README.md`
- Test: backend and frontend test commands.

**Interfaces:**
- Documents env vars, API prefix, and operator flow.

- [ ] **Step 1: Add release documentation**

Append to `README_CN.md`:

```markdown
## 电子发票导入

系统支持上传电子发票批次压缩包。压缩包内每张发票应为一个独立 zip，包含 XML，并可包含 PDF/OFD。系统从 XML 解析发票字段，判断上游/下游，推荐合同候选，并在操作人确认分摊后写入正式挂账记录。

生产环境必须配置：

- `COMPANY_NAME`
- `COMPANY_TAX_NO`

第一期不支持无合同费用发票、OCR、自动拆分金额或自动确认入账。
```

Append to `docs/API_DOCUMENTATION.md`:

```markdown
### 电子发票导入

- `POST /api/v1/invoice-imports/batches` 上传发票批次 zip
- `GET /api/v1/invoice-imports/batches` 查看导入批次
- `GET /api/v1/invoice-imports/batches/{batch_id}/items` 查看批次发票明细
- `POST /api/v1/invoice-imports/items/{item_id}/allocations` 新增分摊
- `PUT /api/v1/invoice-imports/allocations/{allocation_id}` 修改分摊
- `POST /api/v1/invoice-imports/items/{item_id}/confirm` 确认挂账
```

- [ ] **Step 2: Run backend tests**

Run:

```bash
cd backend && pytest tests/test_invoice_import_*.py -v
```

Expected: all invoice import backend tests pass.

- [ ] **Step 3: Run frontend tests**

Run:

```bash
cd frontend && npm run test -- InvoiceImportWorkbench.spec.js
```

Expected: invoice import workbench tests pass.

- [ ] **Step 4: Run release lint if available**

Run:

```bash
cd frontend && npm run lint
```

Expected: lint passes or reports only pre-existing unrelated warnings documented in the final handoff.

- [ ] **Step 5: Commit**

```bash
git add README.md README_CN.md docs/API_DOCUMENTATION.md
git commit -m "docs: document electronic invoice import"
```

---

## Plan Self-Review

Spec coverage:

- Upload nested zip package: covered by Tasks 3, 7, 8.
- XML parsing source of truth: covered by Task 3.
- PDF/OFD/XML preservation: covered by spec and Task 7 service processing.
- Duplicate detection: covered by Task 4 and Task 7.
- Upstream/downstream classification: covered by Task 4.
- Contract candidate matching: covered by Task 4.
- Manual multi-contract allocation: covered by Tasks 5, 8, 9.
- Confirmation into existing invoice tables: covered by Task 5.
- Frontend workbench: covered by Tasks 8 and 9.
- Documentation and verification: covered by Task 10.

Type consistency:

- `InvoiceDirection` values match database direction strings.
- `AllocationCreate` fields match `InvoiceImportAllocation`.
- Posting service trace fields match formal invoice model additions.
- Frontend API paths match router paths.

Execution handoff:

Plan complete and saved to `docs/superpowers/plans/2026-07-08-electronic-invoice-import.md`. Use either subagent-driven execution per task or inline execution with review checkpoints.
