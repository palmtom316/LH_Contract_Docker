"""Electronic invoice import models."""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InvoiceImportBatch(Base):
    """Uploaded invoice import batch."""

    __tablename__ = "invoice_import_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    archive_file_path = Column(String(500), nullable=True)
    archive_file_key = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="uploaded", index=True)
    total_items = Column(Integer, nullable=False, default=0)
    parsed_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    duplicate_items = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    items = relationship("InvoiceImportItem", back_populates="batch", cascade="all, delete-orphan")


class InvoiceImportItem(Base):
    """Single invoice item extracted from a batch."""

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
    """Operator-created allocation from an import item to a contract."""

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
    """Potential contract match for an imported invoice item."""

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
