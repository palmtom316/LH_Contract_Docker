"""
Management Contract Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.enums import ContractCategory, PaymentCategory, PricingMode, ManagementMode

# ===== Contract Management Schemas =====
class ContractManagementBase(BaseModel):
    """Base management contract schema"""
    contract_code: str = Field(..., max_length=50)
    contract_name: str = Field(..., max_length=200)
    
    party_a_name: str = Field(..., max_length=200)
    party_b_name: str = Field(..., max_length=200)
    
    upstream_contract_id: Optional[int] = None
    # upstream_contract_name_snapshot removed
    
    category: Optional[str] = None
    company_category: Optional[str] = None
    pricing_mode: Optional[str] = None
    management_mode: Optional[str] = None
    
    responsible_person: Optional[str] = Field(None, max_length=100)
    
    party_a_contact: Optional[str] = Field(None, max_length=100)
    party_a_phone: Optional[str] = Field(None, max_length=20)
    
    party_b_contact: Optional[str] = Field(None, max_length=100)
    party_b_phone: Optional[str] = Field(None, max_length=20)
    
    contract_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default="执行中", max_length=50)
    notes: Optional[str] = None
    contract_file_path: Optional[str] = None


class ContractManagementCreate(ContractManagementBase):
    serial_number: Optional[int] = Field(None, gt=0, description="合同序号")


class ContractManagementUpdate(BaseModel):
    serial_number: Optional[int] = Field(None, gt=0, description="合同序号")
    contract_code: Optional[str] = Field(None, max_length=50)
    contract_name: Optional[str] = Field(None, max_length=200)
    party_a_name: Optional[str] = Field(None, max_length=200)
    party_b_name: Optional[str] = Field(None, max_length=200)
    
    upstream_contract_id: Optional[int] = None
    upstream_contract_name_snapshot: Optional[str] = Field(None, max_length=200)

    category: Optional[str] = None
    company_category: Optional[str] = None
    pricing_mode: Optional[str] = None
    management_mode: Optional[str] = None
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


class ContractManagementResponse(ContractManagementBase):
    id: int
    serial_number: Optional[int] = None
    upstream_contract_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    # Calculated fields
    total_payable: Optional[Decimal] = None
    total_invoiced: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    total_settlement: Optional[Decimal] = None
    
    # Feishu Approval Integration (V1.4)
    approval_status: Optional[str] = None
    feishu_instance_code: Optional[str] = None
    approval_pdf_path: Optional[str] = None

    class Config:
        from_attributes = True


class ContractManagementListResponse(BaseModel):
    items: List[ContractManagementResponse]
    total: int
    page: int
    page_size: int


# ===== Payable Schemas =====
class ManagementPayableBase(BaseModel):
    category: str
    amount: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=300)
    expected_date: Optional[date] = None
    file_path: Optional[str] = None


class ManagementPayableCreate(ManagementPayableBase):
    contract_id: int


class ManagementPayableResponse(ManagementPayableBase):
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Invoice Management Schemas =====
class ManagementInvoiceBase(BaseModel):
    invoice_number: str = Field(..., max_length=50)
    invoice_date: date
    amount: Decimal = Field(..., ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    invoice_type: Optional[str] = Field(None, max_length=50)
    supplier_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=300)
    file_path: Optional[str] = None


class ManagementInvoiceCreate(ManagementInvoiceBase):
    contract_id: int


class ManagementInvoiceResponse(ManagementInvoiceBase):
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Payment Schemas =====
class ManagementPaymentBase(BaseModel):
    payment_date: date
    amount: Decimal = Field(..., ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    payee_name: Optional[str] = Field(None, max_length=200)
    payee_account: Optional[str] = Field(None, max_length=100)
    payee_bank: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=300)
    file_path: Optional[str] = None


class ManagementPaymentCreate(ManagementPaymentBase):
    contract_id: int


class ManagementPaymentResponse(ManagementPaymentBase):
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Management Settlement Schemas =====
class ManagementSettlementBase(BaseModel):
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


class ManagementSettlementCreate(ManagementSettlementBase):
    contract_id: int


class ManagementSettlementResponse(ManagementSettlementBase):
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
