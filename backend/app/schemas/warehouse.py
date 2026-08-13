"""Warehouse Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.warehouse import (
    CountStatus,
    DocumentStatus,
    DocumentType,
    InboundBusinessType,
    MaterialCategory,
    MaterialCondition,
    OutboundBusinessType,
    SupplyType,
)


class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    manager_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    manager_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class LocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    id: int
    warehouse_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WarehouseResponse(WarehouseBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    locations: List[LocationResponse] = []

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    upstream_contract_id: Optional[int] = None
    is_active: bool = True


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    upstream_contract_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: int
    code: str
    name: str
    upstream_contract_id: Optional[int] = None
    is_active: bool = True
    company_category: Optional[str] = None
    party_a_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpstreamContractLookup(BaseModel):
    id: int
    serial_number: Optional[int] = None
    contract_name: str
    company_category: Optional[str] = None
    party_a_name: Optional[str] = None


class MaterialCreate(BaseModel):
    category: MaterialCategory
    supply_type: SupplyType
    condition: MaterialCondition
    name: str = Field(..., min_length=1, max_length=200)
    brand: str = Field("", max_length=100)
    specification: str = Field("", max_length=200)
    unit: str = Field(..., min_length=1, max_length=20)
    minimum_stock: Decimal = Field(Decimal("0"), ge=0)
    description: Optional[str] = None
    legacy_code: Optional[str] = Field(None, max_length=50)


class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    specification: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    minimum_stock: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    legacy_code: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class MaterialResponse(BaseModel):
    id: int
    code: str
    legacy_code: Optional[str] = None
    category: str
    supply_type: str
    condition: str
    name: str
    brand: str
    specification: str
    unit: str
    minimum_stock: Decimal
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserScopeItem(BaseModel):
    warehouse_id: int
    is_default: bool = False


class UserScopeUpdate(BaseModel):
    scopes: List[UserScopeItem]


class UserScopeResponse(BaseModel):
    user_id: int
    warehouse_id: int
    warehouse_code: Optional[str] = None
    warehouse_name: Optional[str] = None
    is_default: bool

    class Config:
        from_attributes = True


class InboundLineCreate(BaseModel):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    warehouse_id: Optional[int] = None
    location_id: Optional[int] = None
    project_id: Optional[int] = None
    description: Optional[str] = None


class OutboundLineCreate(BaseModel):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    warehouse_id: Optional[int] = None
    location_id: Optional[int] = None
    project_id: Optional[int] = None
    description: Optional[str] = None


class TransferLineCreate(BaseModel):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    source_warehouse_id: int
    source_location_id: int
    source_project_id: int
    target_warehouse_id: int
    target_location_id: int
    target_project_id: int
    description: Optional[str] = None


class InboundCreate(BaseModel):
    warehouse_id: int
    location_id: int
    project_id: int
    occurred_on: date
    handler: str = Field(..., min_length=1, max_length=100)
    business_type: InboundBusinessType
    reference_no: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=80)
    lines: List[InboundLineCreate] = Field(..., min_length=1)


class OutboundCreate(BaseModel):
    warehouse_id: int
    location_id: int
    project_id: int
    occurred_on: date
    handler: str = Field(..., min_length=1, max_length=100)
    business_type: OutboundBusinessType
    reference_no: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=80)
    lines: List[OutboundLineCreate] = Field(..., min_length=1)


class TransferCreate(BaseModel):
    occurred_on: date
    handler: str = Field(..., min_length=1, max_length=100)
    reference_no: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=80)
    lines: List[TransferLineCreate] = Field(..., min_length=1)


class VoidDocumentRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
    idempotency_key: Optional[str] = Field(None, max_length=80)


class DocumentLineResponse(BaseModel):
    id: int
    line_no: int
    material_id: int
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    quantity: Decimal
    source_warehouse_id: Optional[int] = None
    source_location_id: Optional[int] = None
    source_project_id: Optional[int] = None
    target_warehouse_id: Optional[int] = None
    target_location_id: Optional[int] = None
    target_project_id: Optional[int] = None
    source_warehouse_name: Optional[str] = None
    source_location_name: Optional[str] = None
    source_project_name: Optional[str] = None
    target_warehouse_name: Optional[str] = None
    target_location_name: Optional[str] = None
    target_project_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    document_no: str
    document_type: DocumentType | str
    status: DocumentStatus | str
    occurred_on: date
    business_type: Optional[str] = None
    reference_no: Optional[str] = None
    description: Optional[str] = None
    handler: str
    created_by: int
    posted_by: Optional[int] = None
    voided_by: Optional[int] = None
    created_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    reversed_document_id: Optional[int] = None
    lines: List[DocumentLineResponse] = []

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class StockBalanceResponse(BaseModel):
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    quantity: Decimal
    minimum_stock: Decimal = Decimal("0")
    version: int
    warehouse_code: Optional[str] = None
    warehouse_name: Optional[str] = None
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_unit: Optional[str] = None
    supply_type: Optional[str] = None
    condition: Optional[str] = None
    category: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockBalanceListResponse(BaseModel):
    items: List[StockBalanceResponse]
    total: int
    page: int
    page_size: int


class LedgerEntryResponse(BaseModel):
    id: int
    document_id: int
    document_no: Optional[str] = None
    document_type: Optional[str] = None
    document_line_id: int
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    quantity_delta: Decimal
    occurred_on: date
    created_at: Optional[datetime] = None
    warehouse_name: Optional[str] = None
    location_name: Optional[str] = None
    project_name: Optional[str] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None

    class Config:
        from_attributes = True


class LedgerListResponse(BaseModel):
    items: List[LedgerEntryResponse]
    total: int
    page: int
    page_size: int


class CountCreate(BaseModel):
    warehouse_id: int
    location_id: Optional[int] = None
    project_id: Optional[int] = None
    counted_on: date
    description: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=80)


class CountLineUpdate(BaseModel):
    id: int
    counted_quantity: Decimal = Field(..., ge=0)


class CountLinesUpdate(BaseModel):
    lines: List[CountLineUpdate] = Field(..., min_length=1)


class CountLineResponse(BaseModel):
    id: int
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    book_quantity: Decimal
    counted_quantity: Optional[Decimal] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    location_name: Optional[str] = None
    project_name: Optional[str] = None
    adjustment_document_id: Optional[int] = None

    class Config:
        from_attributes = True


class CountResponse(BaseModel):
    id: int
    count_no: str
    warehouse_id: int
    location_id: Optional[int] = None
    project_id: Optional[int] = None
    counted_on: date
    status: CountStatus | str
    description: Optional[str] = None
    created_by: int
    confirmed_by: Optional[int] = None
    created_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    adjustment_document_id: Optional[int] = None
    warehouse_name: Optional[str] = None
    lines: List[CountLineResponse] = []

    class Config:
        from_attributes = True


class CountListResponse(BaseModel):
    items: List[CountResponse]
    total: int
    page: int
    page_size: int


class SupplementUpdate(BaseModel):
    document_line_id: Optional[int] = None
    delivery_note_no: Optional[str] = Field(None, max_length=100)
    acceptance_no: Optional[str] = Field(None, max_length=100)
    contract_no: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    price_type: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    weigh_in: Optional[Decimal] = None
    residual_value: Optional[Decimal] = None
    admin_notes: Optional[str] = None


class SupplementResponse(SupplementUpdate):
    id: int
    document_id: int
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RebuildResult(BaseModel):
    dimensions: int
    mismatches: int
    repaired: bool


class QrPayloadResponse(BaseModel):
    id: int
    kind: str
    payload: str
    label: str
