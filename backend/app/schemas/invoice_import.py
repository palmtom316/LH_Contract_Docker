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
    management_contract_id: Optional[int] = Field(None, gt=0)
    zero_hour_labor_id: Optional[int] = Field(None, gt=0)
    amount: Decimal = Field(..., gt=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=300)

    @model_validator(mode="after")
    def validate_target_contract(self) -> "AllocationCreate":
        if self.direction == InvoiceDirection.UPSTREAM:
            targets = [
                self.upstream_contract_id,
                self.downstream_contract_id,
                self.management_contract_id,
                self.zero_hour_labor_id,
            ]
            if (
                sum(value is not None for value in targets) != 1
                or not self.upstream_contract_id
            ):
                raise ValueError("上游分摊必须且只能选择上游合同")
        if self.direction == InvoiceDirection.DOWNSTREAM:
            targets = [
                self.downstream_contract_id,
                self.management_contract_id,
                self.zero_hour_labor_id,
            ]
            if (
                sum(value is not None for value in targets) != 1
                or self.upstream_contract_id
            ):
                raise ValueError("进项发票分摊必须选择下游、管理合同或零星用工之一")
        if self.direction == InvoiceDirection.UNKNOWN:
            raise ValueError("分摊方向必须为上游或下游")
        return self


class AllocationUpdate(BaseModel):
    direction: Optional[InvoiceDirection] = None
    upstream_contract_id: Optional[int] = Field(None, gt=0)
    downstream_contract_id: Optional[int] = Field(None, gt=0)
    management_contract_id: Optional[int] = Field(None, gt=0)
    zero_hour_labor_id: Optional[int] = Field(None, gt=0)
    amount: Optional[Decimal] = Field(None, gt=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=300)

    @model_validator(mode="after")
    def validate_direction_when_present(self) -> "AllocationUpdate":
        if self.direction == InvoiceDirection.UNKNOWN:
            raise ValueError("分摊方向必须为上游或下游")
        return self


class MatchCandidateResponse(BaseModel):
    id: int
    direction: InvoiceDirection
    upstream_contract_id: Optional[int] = None
    downstream_contract_id: Optional[int] = None
    management_contract_id: Optional[int] = None
    zero_hour_labor_id: Optional[int] = None
    score: int
    matched_signals: Dict[str, Any]
    contract_serial_number: Optional[int] = None
    contract_code: Optional[str] = None
    contract_name: Optional[str] = None

    class Config:
        from_attributes = True


class AllocationResponse(BaseModel):
    id: int
    item_id: int
    direction: InvoiceDirection
    upstream_contract_id: Optional[int] = None
    downstream_contract_id: Optional[int] = None
    management_contract_id: Optional[int] = None
    zero_hour_labor_id: Optional[int] = None
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
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    invoice_type: Optional[str] = None
    remarks: Optional[str] = None
    project_name: Optional[str] = None
    construction_project_name: Optional[str] = None
    direction: InvoiceDirection
    parse_status: str
    match_status: str
    confirmation_status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    ignored_reason: Optional[str] = None
    clear_reason: Optional[str] = None
    posting_version: int = 0
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


class ClearInvoiceRequest(IgnoreItemRequest):
    pass
