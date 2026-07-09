"""Pydantic schemas for electronic invoice import APIs."""
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
