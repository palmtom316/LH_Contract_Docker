from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator


class ReceiptAllocationCreate(BaseModel):
    direction: str
    upstream_contract_id: Optional[int] = None
    downstream_contract_id: Optional[int] = None
    management_contract_id: Optional[int] = None
    zero_hour_labor_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)

    @model_validator(mode="after")
    def target(self):
        targets = [
            self.upstream_contract_id,
            self.downstream_contract_id,
            self.management_contract_id,
            self.zero_hour_labor_id,
        ]
        if sum(x is not None for x in targets) != 1:
            raise ValueError("请选择且只能选择一个入账目标")
        if self.direction not in {"receipt", "payment"}:
            raise ValueError("回单方向无效")
        if self.direction == "receipt" and self.upstream_contract_id is None:
            raise ValueError("收款只能选择上游合同")
        if self.direction == "payment" and self.upstream_contract_id is not None:
            raise ValueError("付款不能选择上游合同")
        return self


class ReceiptAllocationResponse(ReceiptAllocationCreate):
    id: int
    item_id: int
    status: str
    formal_record_id: Optional[int] = None
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReceiptCandidateResponse(BaseModel):
    id: int
    direction: str
    contract_type: str
    contract_id: int
    score: int
    matched_signals: dict[str, Any]
    contract_name: Optional[str] = None

    class Config:
        from_attributes = True


class BankReceiptItemResponse(BaseModel):
    id: int
    batch_id: int
    source_filename: str
    sha256: str
    direction: str
    transaction_at: Optional[datetime] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payer_name: Optional[str] = None
    payer_account: Optional[str] = None
    payee_name: Optional[str] = None
    payee_account: Optional[str] = None
    summary: Optional[str] = None
    bank_serial_number: Optional[str] = None
    status: str
    posting_version: int = 0
    error_message: Optional[str] = None
    ignored_reason: Optional[str] = None
    clear_reason: Optional[str] = None
    allocations: list[ReceiptAllocationResponse] = []
    candidates: list[ReceiptCandidateResponse] = []

    class Config:
        from_attributes = True


class BankReceiptBatchResponse(BaseModel):
    id: int
    batch_number: str
    original_filename: str
    status: str
    confirmed_items: int = 0
    posted_items: int = 0
    job_attempts: int = 0
    job_last_error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClearReceiptRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=300)


class BankReceiptReviewUpdate(BaseModel):
    direction: str
    transaction_at: datetime
    amount: Decimal = Field(..., gt=0)
    currency: str = "CNY"
    payer_name: Optional[str] = None
    payer_account: Optional[str] = None
    payee_name: Optional[str] = None
    payee_account: Optional[str] = None
    summary: Optional[str] = None
    bank_serial_number: Optional[str] = None

    @model_validator(mode="after")
    def direction_valid(self):
        if self.direction not in {"receipt", "payment", "unknown"}:
            raise ValueError("回单方向无效")
        return self
