"""Bank receipt import and auditable posting models."""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BankReceiptBatch(Base):
    __tablename__ = "bank_receipt_batches"
    id = Column(Integer, primary_key=True)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="uploaded", index=True)
    job_attempts = Column(Integer, nullable=False, default=0)
    job_next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)
    job_lease_until = Column(DateTime(timezone=True), nullable=True, index=True)
    job_worker_token = Column(String(64), nullable=True, index=True)
    job_last_error = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    items = relationship("BankReceiptItem", back_populates="batch", cascade="all, delete-orphan")


class BankReceiptItem(Base):
    __tablename__ = "bank_receipt_items"
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("bank_receipt_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    source_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_key = Column(String(500), nullable=True)
    sha256 = Column(String(64), nullable=False, index=True)
    direction = Column(String(20), nullable=False, default="unknown", index=True)
    transaction_at = Column(DateTime(timezone=True), nullable=True, index=True)
    amount = Column(Numeric(15, 2), nullable=True)
    currency = Column(String(20), nullable=True, default="CNY")
    payer_name = Column(String(200), nullable=True)
    payer_account = Column(String(100), nullable=True)
    payee_name = Column(String(200), nullable=True)
    payee_account = Column(String(100), nullable=True)
    summary = Column(String(500), nullable=True)
    bank_serial_number = Column(String(150), nullable=True, index=True)
    raw_mineru_result = Column(JSONB, nullable=True)
    parsed_payload = Column(JSONB, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    status = Column(String(30), nullable=False, default="needs_review", index=True)
    error_message = Column(Text, nullable=True)
    ignored_reason = Column(String(300), nullable=True)
    ignored_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    ignored_at = Column(DateTime(timezone=True), nullable=True)
    clear_reason = Column(String(300), nullable=True)
    cleared_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    posting_version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    batch = relationship("BankReceiptBatch", back_populates="items")
    allocations = relationship("BankReceiptAllocation", back_populates="item", cascade="all, delete-orphan")
    candidates = relationship("BankReceiptMatchCandidate", back_populates="item", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_bank_receipt_sha256"),
        Index("uq_bank_receipt_serial", "bank_serial_number", unique=True, postgresql_where=text("bank_serial_number IS NOT NULL")),
    )


class BankReceiptAllocation(Base):
    __tablename__ = "bank_receipt_allocations"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("bank_receipt_items.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(20), nullable=False)
    upstream_contract_id = Column(Integer, ForeignKey("contracts_upstream.id", ondelete="RESTRICT"), nullable=True)
    downstream_contract_id = Column(Integer, ForeignKey("contracts_downstream.id", ondelete="RESTRICT"), nullable=True)
    management_contract_id = Column(Integer, ForeignKey("contracts_management.id", ondelete="RESTRICT"), nullable=True)
    zero_hour_labor_id = Column(Integer, ForeignKey("zero_hour_labor.id", ondelete="RESTRICT"), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    formal_record_id = Column(Integer, nullable=True)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    item = relationship("BankReceiptItem", back_populates="allocations")


class BankReceiptMatchCandidate(Base):
    __tablename__ = "bank_receipt_match_candidates"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("bank_receipt_items.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(20), nullable=False)
    contract_type = Column(String(20), nullable=False)
    contract_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    matched_signals = Column(JSONB, nullable=False, default=dict)
    contract_name = Column(String(500), nullable=True)
    item = relationship("BankReceiptItem", back_populates="candidates")
