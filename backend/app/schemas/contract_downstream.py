"""
Downstream Contract Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.contract_downstream import PayableCategory


# ===== Contract Downstream Schemas =====
class ContractDownstreamBase(BaseModel):
    """Base downstream contract schema"""
    contract_code: str = Field(..., max_length=50)
    contract_name: str = Field(..., max_length=200)
    supplier_name: str = Field(..., max_length=200)
    supplier_contact: Optional[str] = Field(None, max_length=100)
    supplier_phone: Optional[str] = Field(None, max_length=20)
    upstream_contract_id: Optional[int] = None
    category: Optional[str] = Field(None, max_length=50)
    contract_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default="进行中", max_length=50)
    notes: Optional[str] = None


class ContractDownstreamCreate(ContractDownstreamBase):
    """Schema for creating downstream contract"""
    pass


class ContractDownstreamUpdate(BaseModel):
    """Schema for updating downstream contract"""
    contract_name: Optional[str] = Field(None, max_length=200)
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_contact: Optional[str] = Field(None, max_length=100)
    supplier_phone: Optional[str] = Field(None, max_length=20)
    upstream_contract_id: Optional[int] = None
    category: Optional[str] = Field(None, max_length=50)
    contract_amount: Optional[Decimal] = Field(None, ge=0)
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class ContractDownstreamResponse(ContractDownstreamBase):
    """Schema for downstream contract response"""
    id: int
    contract_file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    # Calculated fields
    total_payable: Optional[Decimal] = None
    total_invoiced: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ContractDownstreamListResponse(BaseModel):
    """Schema for paginated downstream contracts list"""
    items: List[ContractDownstreamResponse]
    total: int
    page: int
    page_size: int


# ===== Payable Schemas =====
class PayableBase(BaseModel):
    """Base payable schema"""
    category: PayableCategory
    amount: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=300)
    expected_date: Optional[date] = None


class PayableCreate(PayableBase):
    """Schema for creating payable"""
    contract_id: int


class PayableResponse(PayableBase):
    """Schema for payable response"""
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Invoice Downstream Schemas =====
class InvoiceDownstreamBase(BaseModel):
    """Base downstream invoice schema"""
    invoice_number: str = Field(..., max_length=50)
    invoice_date: date
    amount: Decimal = Field(..., ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    invoice_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=300)


class InvoiceDownstreamCreate(InvoiceDownstreamBase):
    """Schema for creating downstream invoice"""
    contract_id: int


class InvoiceDownstreamResponse(InvoiceDownstreamBase):
    """Schema for downstream invoice response"""
    id: int
    contract_id: int
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Payment Schemas =====
class PaymentBase(BaseModel):
    """Base payment schema"""
    payment_date: date
    amount: Decimal = Field(..., ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    payee_name: Optional[str] = Field(None, max_length=200)
    payee_account: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=300)


class PaymentCreate(PaymentBase):
    """Schema for creating payment"""
    contract_id: int


class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    id: int
    contract_id: int
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Downstream Settlement Schemas =====
class DownstreamSettlementBase(BaseModel):
    """Base downstream settlement schema"""
    settlement_code: str = Field(..., max_length=50)
    settlement_date: date
    settlement_amount: Decimal = Field(..., ge=0)
    audit_amount: Optional[Decimal] = Field(None, ge=0)
    final_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(default="待审核", max_length=50)
    description: Optional[str] = None


class DownstreamSettlementCreate(DownstreamSettlementBase):
    """Schema for creating downstream settlement"""
    contract_id: int


class DownstreamSettlementResponse(DownstreamSettlementBase):
    """Schema for downstream settlement response"""
    id: int
    contract_id: int
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
