from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class ZeroHourLaborBase(BaseModel):
    labor_date: date
    attribution: str  # COMPANY/PROJECT
    
    upstream_contract_id: Optional[int] = None
    dispatch_unit: Optional[str] = None
    dispatch_file_path: Optional[str] = None
    dispatch_file_key: Optional[str] = None
    dispatch_file_storage: Optional[str] = "local"
    
    # Skilled Labor (技工)
    skilled_unit_price: Decimal = 0
    skilled_quantity: Decimal = 0
    skilled_price_total: Decimal = 0
    
    # General Labor (普工)
    general_unit_price: Decimal = 0
    general_quantity: Decimal = 0
    general_price_total: Decimal = 0
    
    # Legacy fields (for backward compatibility)
    labor_type: Optional[str] = None
    labor_unit_price: Decimal = 0
    labor_quantity: Decimal = 0
    labor_price_total: Decimal = 0
    
    vehicle_quantity: Decimal = 0
    vehicle_unit_price: Decimal = 0
    vehicle_price_total: Decimal = 0

    description: Optional[str] = None  # 零星用工说明
    tax_rate: Decimal = 0  # 税率 (%)
    tax_amount: Decimal = 0  # 税金

    total_amount: Decimal = 0  # 含税总金额

class ZeroHourLaborMaterialBase(BaseModel):
    material_name: str
    material_unit: Optional[str] = None
    material_quantity: Decimal = 0
    material_unit_price: Decimal = 0
    material_price_total: Decimal = 0

class ZeroHourLaborMaterialCreate(ZeroHourLaborMaterialBase):
    pass

class ZeroHourLaborMaterialResponse(ZeroHourLaborMaterialBase):
    id: int
    zero_hour_labor_id: int
    class Config:
        from_attributes = True

class ZeroHourLaborCreate(ZeroHourLaborBase):
    materials: List[ZeroHourLaborMaterialCreate] = []

class ZeroHourLaborUpdate(BaseModel):
    labor_date: Optional[date] = None
    attribution: Optional[str] = None
    upstream_contract_id: Optional[int] = None
    dispatch_unit: Optional[str] = None
    dispatch_file_path: Optional[str] = None

    skilled_unit_price: Optional[Decimal] = None
    skilled_quantity: Optional[Decimal] = None
    skilled_price_total: Optional[Decimal] = None
    general_unit_price: Optional[Decimal] = None
    general_quantity: Optional[Decimal] = None
    general_price_total: Optional[Decimal] = None

    labor_type: Optional[str] = None
    labor_unit_price: Optional[Decimal] = None
    labor_quantity: Optional[Decimal] = None
    labor_price_total: Optional[Decimal] = None
    vehicle_quantity: Optional[Decimal] = None
    vehicle_unit_price: Optional[Decimal] = None
    vehicle_price_total: Optional[Decimal] = None

    description: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None

    total_amount: Optional[Decimal] = None
    materials: Optional[List[ZeroHourLaborMaterialCreate]] = None

class UpstreamContractRef(BaseModel):
    id: int
    contract_name: str
    contract_code: Optional[str] = None
    class Config:
        from_attributes = True

class ZeroHourLaborResponse(ZeroHourLaborBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    upstream_contract: Optional[UpstreamContractRef] = None
    materials: List[ZeroHourLaborMaterialResponse] = []

    material_price_total: Decimal = 0

    approval_status: Optional[str] = None
    feishu_instance_code: Optional[str] = None
    approval_pdf_path: Optional[str] = None
    approval_pdf_key: Optional[str] = None
    approval_pdf_storage: Optional[str] = "local"

    @field_validator(
        "skilled_unit_price",
        "skilled_quantity",
        "skilled_price_total",
        "general_unit_price",
        "general_quantity",
        "general_price_total",
        "labor_unit_price",
        "labor_quantity",
        "labor_price_total",
        "vehicle_quantity",
        "vehicle_unit_price",
        "vehicle_price_total",
        "tax_rate",
        "tax_amount",
        "total_amount",
        "material_price_total",
        mode="before",
    )
    @classmethod
    def coerce_null_decimals_to_zero(cls, value):
        return Decimal("0") if value is None else value

    class Config:
        from_attributes = True

class ZeroHourFinanceBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
class ZeroHourPayableCreate(ZeroHourFinanceBase):
    category: str; expected_date: Optional[date]=None; description: Optional[str]=None; file_path:Optional[str]=None; file_key:Optional[str]=None
class ZeroHourInvoiceCreate(ZeroHourFinanceBase):
    invoice_date: date; invoice_number: str; tax_amount: Decimal=0; supplier: Optional[str]=None; file_path:Optional[str]=None; file_key:Optional[str]=None
class ZeroHourPaymentCreate(ZeroHourFinanceBase):
    payment_date: date; payee_name: Optional[str]=None; payee_account: Optional[str]=None; payee_bank: Optional[str]=None; payment_method: Optional[str]=None; file_path:Optional[str]=None; file_key:Optional[str]=None
class ZeroHourFinanceResponse(BaseModel):
    id:int; zero_hour_labor_id:int; amount:Decimal; file_path:Optional[str]=None; file_key:Optional[str]=None; status:Optional[str]=None; created_at:Optional[datetime]=None
    class Config: from_attributes=True
class ZeroHourLaborDetailResponse(ZeroHourLaborResponse):
    payables: list[dict]=[]; invoices:list[dict]=[]; payments:list[dict]=[]
    payable_total:Decimal=0; invoiced_total:Decimal=0; paid_total:Decimal=0; unpaid_total:Decimal=0

class ZeroHourLaborListResponse(BaseModel):
    items: List[ZeroHourLaborResponse]
    total: int
    page: int
    page_size: int
