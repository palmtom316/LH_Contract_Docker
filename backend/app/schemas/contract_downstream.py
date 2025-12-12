"""
Downstream Contract Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.enums import ContractCategory, DownstreamContractCategory, PaymentCategory, PricingMode, ManagementMode

# ===== Contract Downstream Schemas =====
class ContractDownstreamBase(BaseModel):
    """Base downstream contract schema"""
    contract_code: str = Field(..., max_length=50)
    contract_name: str = Field(..., max_length=200)
    
    party_a_name: str = Field(..., max_length=200) # Added (Req 3.3)
    party_b_name: str = Field(..., max_length=200) # Renamed from supplier_name
    
    upstream_contract_id: Optional[int] = None
    upstream_contract_name_snapshot: Optional[str] = Field(None, max_length=200) # Added
    
    # Classification (Req 3.3: Same structure as Upstream)
    category: Optional[str] = None  # 合同类别 - 使用字符串
    company_category: Optional[str] = None
    pricing_mode: Optional[PricingMode] = None
    management_mode: Optional[ManagementMode] = None
    
    responsible_person: Optional[str] = Field(None, max_length=100)
    
    party_a_contact: Optional[str] = Field(None, max_length=100)
    party_a_phone: Optional[str] = Field(None, max_length=20)
    
    party_b_contact: Optional[str] = Field(None, max_length=100) # Renamed from supplier_contact
    party_b_phone: Optional[str] = Field(None, max_length=20)
    
    contract_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default="执行中", max_length=50)
    notes: Optional[str] = None
    contract_file_path: Optional[str] = None # Added for PDF


class ContractDownstreamCreate(ContractDownstreamBase):
    """Schema for creating downstream contract"""
    id: int = Field(..., gt=0, description="合同序号，必须是大于0的整数")


class ContractDownstreamUpdate(BaseModel):
    """Schema for updating downstream contract"""
    id: Optional[int] = Field(None, gt=0, description="合同序号")
    contract_code: Optional[str] = Field(None, max_length=50)
    contract_name: Optional[str] = Field(None, max_length=200)
    party_a_name: Optional[str] = Field(None, max_length=200)
    party_b_name: Optional[str] = Field(None, max_length=200)
    
    upstream_contract_id: Optional[int] = None
    upstream_contract_name_snapshot: Optional[str] = Field(None, max_length=200)

    category: Optional[str] = None
    company_category: Optional[str] = None
    pricing_mode: Optional[PricingMode] = None
    management_mode: Optional[ManagementMode] = None
    responsible_person: Optional[str] = Field(None, max_length=100)
    
    party_a_contact: Optional[str] = Field(None, max_length=100)
    party_a_phone: Optional[str] = Field(None, max_length=20)
    party_b_contact: Optional[str] = Field(None, max_length=100)
    party_b_phone: Optional[str] = Field(None, max_length=20)
    
    contract_amount: Optional[Decimal] = Field(None, ge=0)
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    contract_file_path: Optional[str] = None


class ContractDownstreamResponse(ContractDownstreamBase):
    """Schema for downstream contract response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    # Calculated fields
    total_payable: Optional[Decimal] = None
    total_invoiced: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    total_settlement: Optional[Decimal] = None

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
    category: PaymentCategory
    amount: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=300)
    expected_date: Optional[date] = None
    file_path: Optional[str] = None


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
    supplier_name: Optional[str] = Field(None, max_length=200) # Optional override or match party B
    description: Optional[str] = Field(None, max_length=300)
    file_path: Optional[str] = None


class InvoiceDownstreamCreate(InvoiceDownstreamBase):
    """Schema for creating downstream invoice"""
    contract_id: int


class InvoiceDownstreamResponse(InvoiceDownstreamBase):
    """Schema for downstream invoice response"""
    id: int
    contract_id: int
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
    payee_bank: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=300)
    file_path: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating payment"""
    contract_id: int


class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Downstream Settlement Schemas =====
class DownstreamSettlementBase(BaseModel):
    """Base downstream settlement schema"""
    settlement_code: Optional[str] = Field(None, max_length=50)
    settlement_date: date
    completion_date: Optional[date] = None
    warranty_date: Optional[date] = None
    settlement_amount: Decimal = Field(..., ge=0)
    audit_amount: Optional[Decimal] = Field(None, ge=0)
    final_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(default="待审核", max_length=50)
    description: Optional[str] = None
    file_path: Optional[str] = None


class DownstreamSettlementCreate(DownstreamSettlementBase):
    """Schema for creating downstream settlement"""
    contract_id: int


class DownstreamSettlementResponse(DownstreamSettlementBase):
    """Schema for downstream settlement response"""
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
