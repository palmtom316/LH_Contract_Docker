from pydantic import BaseModel, Field
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
    
    total_amount: Decimal = 0

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
    
    class Config:
        from_attributes = True

class ZeroHourLaborListResponse(BaseModel):
    items: List[ZeroHourLaborResponse]
    total: int
    page: int
    page_size: int
