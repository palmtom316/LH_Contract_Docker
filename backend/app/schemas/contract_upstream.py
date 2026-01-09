"""
Upstream Contract Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.enums import ContractCategory, PaymentCategory, ReceivableCategory, PricingMode, ManagementMode


# ===== Contract Upstream Schemas =====
class ContractUpstreamBase(BaseModel):
    """Base upstream contract schema"""
    contract_code: str = Field(..., max_length=50)
    contract_name: str = Field(..., max_length=200)
    party_a_name: str = Field(..., max_length=200)
    party_b_name: str = Field(..., max_length=200)
    
    # Classification - Use str to match database VARCHAR columns
    category: Optional[str] = None
    company_category: Optional[str] = None 
    pricing_mode: Optional[str] = None
    management_mode: Optional[str] = None
    
    responsible_person: Optional[str] = Field(None, max_length=100)
    contract_handler: Optional[str] = Field(None, max_length=100)
    archive_number: Optional[str] = Field(None, max_length=100)
    
    party_a_contact: Optional[str] = Field(None, max_length=100)
    party_a_phone: Optional[str] = Field(None, max_length=20)
    
    project_name: Optional[str] = Field(None, max_length=200)
    project_location: Optional[str] = Field(None, max_length=300)
    
    contract_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default="执行中", max_length=50)
    notes: Optional[str] = None
    contract_file_path: Optional[str] = None


class ContractUpstreamCreate(ContractUpstreamBase):
    """Schema for creating upstream contract"""
    serial_number: Optional[int] = Field(None, gt=0, description="合同序号")


class ContractUpstreamUpdate(BaseModel):
    """Schema for updating upstream contract"""
    serial_number: Optional[int] = Field(None, gt=0, description="合同序号")
    contract_code: Optional[str] = Field(None, max_length=50)
    contract_name: Optional[str] = Field(None, max_length=200)
    party_a_name: Optional[str] = Field(None, max_length=200)
    party_b_name: Optional[str] = Field(None, max_length=200)
    
    category: Optional[str] = None
    company_category: Optional[str] = None
    pricing_mode: Optional[str] = None
    management_mode: Optional[str] = None
    responsible_person: Optional[str] = Field(None, max_length=100)
    contract_handler: Optional[str] = Field(None, max_length=100)
    archive_number: Optional[str] = Field(None, max_length=100)

    party_a_contact: Optional[str] = Field(None, max_length=100)
    party_a_phone: Optional[str] = Field(None, max_length=20)
    project_name: Optional[str] = Field(None, max_length=200)
    project_location: Optional[str] = Field(None, max_length=300)
    
    contract_amount: Optional[Decimal] = Field(None, ge=0)
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    contract_file_path: Optional[str] = None


class ContractUpstreamResponse(ContractUpstreamBase):
    """Schema for upstream contract response"""
    id: int
    serial_number: Optional[int] = None
    contract_file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    # Calculated fields
    total_receivable: Optional[Decimal] = None
    total_invoiced: Optional[Decimal] = None
    total_received: Optional[Decimal] = None
    total_settlement: Optional[Decimal] = None
    
    # Settlement details
    completion_date: Optional[date] = None
    audit_report_path: Optional[str] = None
    start_report_path: Optional[str] = None
    completion_report_path: Optional[str] = None
    
    # Feishu Approval Integration (V1.4)
    approval_status: Optional[str] = None
    feishu_instance_code: Optional[str] = None
    approval_pdf_path: Optional[str] = None

    class Config:
        from_attributes = True


class ContractUpstreamListResponse(BaseModel):
    """Schema for paginated upstream contracts list"""
    items: List[ContractUpstreamResponse]
    total: int
    page: int
    page_size: int


# ===== Receivable Schemas =====
class ReceivableBase(BaseModel):
    """Base receivable schema"""
    category: str
    amount: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=300)
    expected_date: Optional[date] = None
    file_path: Optional[str] = None


class ReceivableCreate(ReceivableBase):
    """Schema for creating receivable"""
    contract_id: int


class ReceivableResponse(ReceivableBase):
    """Schema for receivable response"""
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Invoice Upstream Schemas =====
class InvoiceUpstreamBase(BaseModel):
    """Base upstream invoice schema"""
    invoice_number: str = Field(..., max_length=50)
    invoice_date: date
    amount: Decimal = Field(..., ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    invoice_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=300)
    file_path: Optional[str] = None


class InvoiceUpstreamCreate(InvoiceUpstreamBase):
    """Schema for creating upstream invoice"""
    contract_id: int


class InvoiceUpstreamResponse(InvoiceUpstreamBase):
    """Schema for upstream invoice response"""
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Receipt Schemas =====
class ReceiptBase(BaseModel):
    """Base receipt schema"""
    receipt_date: date
    amount: Decimal = Field(..., ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    payer_name: Optional[str] = Field(None, max_length=200)
    payer_account: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    file_path: Optional[str] = None


class ReceiptCreate(ReceiptBase):
    """Schema for creating receipt"""
    contract_id: int


class ReceiptResponse(ReceiptBase):
    """Schema for receipt response"""
    id: int
    contract_id: int
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Settlement Schemas =====
class SettlementBase(BaseModel):
    """Base settlement schema"""
    settlement_code: str = Field(..., max_length=50)
    settlement_date: date
    completion_date: Optional[date] = None
    warranty_date: Optional[date] = None
    settlement_amount: Decimal = Field(..., ge=0)
    audit_amount: Optional[Decimal] = Field(None, ge=0)
    final_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(default="待审核", max_length=50)
    description: Optional[str] = None
    file_path: Optional[str] = None
    audit_report_path: Optional[str] = None  # 结算审核报告
    start_report_path: Optional[str] = None  # 开工报告
    completion_report_path: Optional[str] = None  # 竣工报告


class SettlementCreate(SettlementBase):
    """Schema for creating settlement"""
    contract_id: int


class SettlementResponse(SettlementBase):
    """Schema for settlement response"""
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
