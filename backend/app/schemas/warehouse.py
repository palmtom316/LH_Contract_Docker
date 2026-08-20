"""Warehouse Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

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
    address: str | None = Field(None, max_length=255)
    manager_name: str | None = Field(None, max_length=100)
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    address: str | None = Field(None, max_length=255)
    manager_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class LocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    is_default: bool = False
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class LocationResponse(LocationBase):
    id: int
    warehouse_id: int
    warehouse_name: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class WarehouseResponse(WarehouseBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    locations: list[LocationResponse] = []

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=200)
    upstream_contract_id: int | None = None
    is_active: bool = True


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    upstream_contract_id: int | None = None
    is_active: bool | None = None


class ProjectResponse(BaseModel):
    id: int
    code: str
    name: str
    upstream_contract_id: int | None = None
    is_active: bool = True
    company_category: str | None = None
    party_a_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class UpstreamContractLookup(BaseModel):
    id: int
    serial_number: int | None = None
    contract_name: str
    company_category: str | None = None
    party_a_name: str | None = None


class MaterialCreate(BaseModel):
    category: MaterialCategory
    supply_type: SupplyType
    condition: MaterialCondition
    name: str = Field(..., min_length=1, max_length=200)
    brand: str = Field("", max_length=100)
    specification: str = Field("", max_length=200)
    unit: str = Field(..., min_length=1, max_length=20)
    quantity_scale: int = Field(3, ge=0, le=4)
    tracks_batch: bool = False
    tracks_serial: bool = False
    shelf_life_days: int | None = Field(None, ge=1)
    minimum_stock: Decimal = Field(Decimal(0), ge=0)
    description: str | None = None
    legacy_code: str | None = Field(None, max_length=50)


class MaterialUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    brand: str | None = Field(None, max_length=100)
    specification: str | None = Field(None, max_length=200)
    unit: str | None = Field(None, min_length=1, max_length=20)
    quantity_scale: int | None = Field(None, ge=0, le=4)
    tracks_batch: bool | None = None
    tracks_serial: bool | None = None
    shelf_life_days: int | None = Field(None, ge=1)
    minimum_stock: Decimal | None = Field(None, ge=0)
    description: str | None = None
    legacy_code: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class MaterialResponse(BaseModel):
    id: int
    code: str
    legacy_code: str | None = None
    category: str
    supply_type: str
    condition: str
    name: str
    brand: str
    specification: str
    unit: str
    quantity_scale: int = 3
    tracks_batch: bool = False
    tracks_serial: bool = False
    shelf_life_days: int | None = None
    minimum_stock: Decimal
    description: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class UserScopeItem(BaseModel):
    warehouse_id: int
    is_default: bool = False


class UserScopeUpdate(BaseModel):
    scopes: list[UserScopeItem]


class UserScopeResponse(BaseModel):
    user_id: int
    warehouse_id: int
    warehouse_code: str | None = None
    warehouse_name: str | None = None
    is_default: bool

    class Config:
        from_attributes = True


class TraceFields(BaseModel):
    batch_no: str | None = Field(None, max_length=100)
    serial_no: str | None = Field(None, max_length=100)
    heat_no: str | None = Field(None, max_length=100)
    production_date: date | None = None
    expiry_date: date | None = None


class InboundLineCreate(TraceFields):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    warehouse_id: int | None = None
    location_id: int | None = None
    project_id: int | None = None
    description: str | None = None


class OutboundLineCreate(TraceFields):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    warehouse_id: int | None = None
    location_id: int | None = None
    project_id: int | None = None
    description: str | None = None


class TransferLineCreate(TraceFields):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    source_warehouse_id: int
    source_location_id: int
    source_project_id: int
    target_warehouse_id: int
    target_location_id: int
    target_project_id: int
    description: str | None = None


class VoucherFields(BaseModel):
    supplier_name: str | None = Field(None, max_length=200)
    purchase_order_no: str | None = Field(None, max_length=100)
    delivery_note_no: str | None = Field(None, max_length=100)
    acceptance_no: str | None = Field(None, max_length=100)
    acceptor: str | None = Field(None, max_length=100)
    qc_result: str | None = Field(None, max_length=50)
    manufacturer: str | None = Field(None, max_length=200)
    batch_no: str | None = Field(None, max_length=100)
    requisition_no: str | None = Field(None, max_length=100)
    work_package: str | None = Field(None, max_length=200)
    crew_name: str | None = Field(None, max_length=100)
    requester_name: str | None = Field(None, max_length=100)
    receiver_name: str | None = Field(None, max_length=100)
    signed_off: bool = False
    scrap_weight: Decimal | None = Field(None, ge=0)
    scrap_assessed_value: Decimal | None = Field(None, ge=0)
    scrap_disposal_method: str | None = Field(None, max_length=50)
    scrap_recycler: str | None = Field(None, max_length=200)
    scrap_residual_value: Decimal | None = Field(None, ge=0)


class InboundCreate(VoucherFields):
    warehouse_id: int
    location_id: int
    project_id: int
    occurred_on: date
    handler: str = Field(..., min_length=1, max_length=100)
    business_type: InboundBusinessType
    reference_no: str | None = Field(None, max_length=100)
    description: str | None = None
    delivery_note_file: str | None = Field(None, max_length=500)
    delivery_note_file_name: str | None = Field(None, max_length=255)
    idempotency_key: str | None = Field(None, max_length=80)
    lines: list[InboundLineCreate] = Field(..., min_length=1)


class OutboundCreate(VoucherFields):
    warehouse_id: int
    location_id: int
    project_id: int
    occurred_on: date
    handler: str = Field(..., min_length=1, max_length=100)
    business_type: OutboundBusinessType
    reference_no: str | None = Field(None, max_length=100)
    description: str | None = None
    scrap_basis_file: str | None = Field(None, max_length=500)
    scrap_basis_file_name: str | None = Field(None, max_length=255)
    idempotency_key: str | None = Field(None, max_length=80)
    lines: list[OutboundLineCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def require_scrap_basis_file(self) -> OutboundCreate:
        if (
            self.business_type == OutboundBusinessType.SCRAP_DISPOSAL
            and not self.scrap_basis_file
        ):
            raise ValueError("选择废旧处理必须上传废旧处理依据文件")
        return self


class TransferCreate(BaseModel):
    occurred_on: date
    handler: str = Field(..., min_length=1, max_length=100)
    reference_no: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    idempotency_key: str | None = Field(None, max_length=80)
    lines: list[TransferLineCreate] = Field(..., min_length=1)


class VoidDocumentRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
    idempotency_key: str | None = Field(None, max_length=80)


class DocumentLineResponse(BaseModel):
    id: int
    line_no: int
    material_id: int
    material_code: str | None = None
    material_name: str | None = None
    material_unit: str | None = None
    quantity: Decimal
    batch_no: str | None = None
    serial_no: str | None = None
    heat_no: str | None = None
    production_date: date | None = None
    expiry_date: date | None = None
    source_warehouse_id: int | None = None
    source_location_id: int | None = None
    source_project_id: int | None = None
    target_warehouse_id: int | None = None
    target_location_id: int | None = None
    target_project_id: int | None = None
    source_warehouse_name: str | None = None
    source_location_name: str | None = None
    source_project_name: str | None = None
    target_warehouse_name: str | None = None
    target_location_name: str | None = None
    target_project_name: str | None = None
    description: str | None = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    document_no: str
    document_type: DocumentType | str
    status: DocumentStatus | str
    occurred_on: date
    business_type: str | None = None
    reference_no: str | None = None
    description: str | None = None
    handler: str
    created_by: int
    posted_by: int | None = None
    voided_by: int | None = None
    created_at: datetime | None = None
    posted_at: datetime | None = None
    voided_at: datetime | None = None
    void_reason: str | None = None
    delivery_note_file: str | None = None
    delivery_note_file_name: str | None = None
    scrap_basis_file: str | None = None
    scrap_basis_file_name: str | None = None
    supplier_name: str | None = None
    purchase_order_no: str | None = None
    delivery_note_no: str | None = None
    acceptance_no: str | None = None
    acceptor: str | None = None
    qc_result: str | None = None
    manufacturer: str | None = None
    batch_no: str | None = None
    requisition_no: str | None = None
    work_package: str | None = None
    crew_name: str | None = None
    requester_name: str | None = None
    receiver_name: str | None = None
    signed_off: bool = False
    scrap_status: str | None = None
    scrap_weight: Decimal | None = None
    scrap_assessed_value: Decimal | None = None
    scrap_disposal_method: str | None = None
    scrap_recycler: str | None = None
    scrap_residual_value: Decimal | None = None
    scrap_settled_at: datetime | None = None
    reversed_document_id: int | None = None
    lines: list[DocumentLineResponse] = []

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class StockBalanceResponse(BaseModel):
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    batch_no: str | None = None
    serial_no: str | None = None
    expiry_date: date | None = None
    quantity: Decimal
    minimum_stock: Decimal = Decimal(0)
    version: int
    warehouse_code: str | None = None
    warehouse_name: str | None = None
    location_code: str | None = None
    location_name: str | None = None
    project_code: str | None = None
    project_name: str | None = None
    material_code: str | None = None
    material_name: str | None = None
    material_unit: str | None = None
    supply_type: str | None = None
    condition: str | None = None
    category: str | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class StockBalanceListResponse(BaseModel):
    items: list[StockBalanceResponse]
    total: int
    page: int
    page_size: int


class LedgerEntryResponse(BaseModel):
    id: int
    document_id: int
    document_no: str | None = None
    document_type: str | None = None
    document_line_id: int
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    batch_no: str | None = None
    serial_no: str | None = None
    expiry_date: date | None = None
    quantity_delta: Decimal
    occurred_on: date
    business_type: str | None = None
    handler: str | None = None
    category: str | None = None
    supply_type: str | None = None
    condition: str | None = None
    created_at: datetime | None = None
    warehouse_name: str | None = None
    location_name: str | None = None
    project_name: str | None = None
    material_code: str | None = None
    material_name: str | None = None

    class Config:
        from_attributes = True


class LedgerListResponse(BaseModel):
    items: list[LedgerEntryResponse]
    total: int
    page: int
    page_size: int


class CountCreate(BaseModel):
    warehouse_id: int
    location_id: int | None = None
    project_id: int | None = None
    counted_on: date
    description: str | None = None
    idempotency_key: str | None = Field(None, max_length=80)


class CountLineUpdate(BaseModel):
    id: int
    counted_quantity: Decimal = Field(..., ge=0)
    variance_reviewed: bool | None = None
    variance_note: str | None = None


class CountLinesUpdate(BaseModel):
    lines: list[CountLineUpdate] = Field(..., min_length=1)


class CountLineResponse(BaseModel):
    id: int
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    batch_no: str | None = None
    serial_no: str | None = None
    expiry_date: date | None = None
    book_quantity: Decimal
    counted_quantity: Decimal | None = None
    variance_reviewed: bool = False
    variance_note: str | None = None
    material_code: str | None = None
    material_name: str | None = None
    material_unit: str | None = None
    location_name: str | None = None
    project_name: str | None = None

    class Config:
        from_attributes = True


class CountResponse(BaseModel):
    id: int
    count_no: str
    warehouse_id: int
    location_id: int | None = None
    project_id: int | None = None
    counted_on: date
    snapshot_at: datetime | None = None
    snapshot_source: str | None = None
    status: CountStatus | str
    description: str | None = None
    void_reason: str | None = None
    review_notes: str | None = None
    created_by: int
    confirmed_by: int | None = None
    reviewed_by: int | None = None
    voided_by: int | None = None
    created_at: datetime | None = None
    confirmed_at: datetime | None = None
    reviewed_at: datetime | None = None
    voided_at: datetime | None = None
    reopened_from_id: int | None = None
    adjustment_document_id: int | None = None
    warehouse_name: str | None = None
    lines: list[CountLineResponse] = []

    class Config:
        from_attributes = True


class CountListResponse(BaseModel):
    items: list[CountResponse]
    total: int
    page: int
    page_size: int


class SupplementUpdate(BaseModel):
    document_line_id: int | None = None
    delivery_note_no: str | None = Field(None, max_length=100)
    acceptance_no: str | None = Field(None, max_length=100)
    contract_no: str | None = Field(None, max_length=100)
    manufacturer: str | None = Field(None, max_length=200)
    price_type: str | None = Field(None, max_length=50)
    unit_price: Decimal | None = Field(None, ge=0)
    amount: Decimal | None = Field(None, ge=0)
    weigh_in: Decimal | None = Field(None, ge=0)
    residual_value: Decimal | None = Field(None, ge=0)
    admin_notes: str | None = None


class SupplementResponse(SupplementUpdate):
    id: int
    document_id: int
    version: int = 1
    updated_by: int | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class RebuildDifference(BaseModel):
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    batch_no: str | None = None
    serial_no: str | None = None
    current: str
    expected: str


class RebuildRequest(BaseModel):
    repair: bool = False
    reason: str | None = Field(None, max_length=500)


class RebuildResult(BaseModel):
    id: int | None = None
    dimensions: int
    mismatches: int
    repaired: bool
    dry_run: bool = True
    reason: str | None = None
    differences: list[RebuildDifference] = []


class PeriodResponse(BaseModel):
    id: int
    year: int
    month: int
    status: str
    closed_by: int | None = None
    closed_at: datetime | None = None
    reopened_by: int | None = None
    reopened_at: datetime | None = None
    reopen_reason: str | None = None
    opened_by: int | None = None
    opened_at: datetime | None = None
    open_reason: str | None = None

    class Config:
        from_attributes = True


class PeriodActionRequest(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    reason: str | None = Field(None, max_length=500)


class CountActionRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, max_length=500)
    description: str | None = Field(None, max_length=500)


class UnitResponse(BaseModel):
    id: int
    code: str
    name: str
    aliases: str | None = None
    is_active: bool = True

    class Config:
        from_attributes = True


class UnitConversionResponse(BaseModel):
    id: int
    from_unit_id: int
    to_unit_id: int
    factor: Decimal
    from_unit_code: str | None = None
    to_unit_code: str | None = None

    class Config:
        from_attributes = True


class ReportRow(BaseModel):
    warehouse_id: int | None = None
    warehouse_name: str | None = None
    project_id: int | None = None
    project_name: str | None = None
    material_id: int | None = None
    material_code: str | None = None
    material_name: str | None = None
    material_unit: str | None = None
    inbound_qty: Decimal = Decimal(0)
    outbound_qty: Decimal = Decimal(0)
    quantity: Decimal = Decimal(0)
    minimum_stock: Decimal = Decimal(0)
    last_moved_on: date | None = None
    idle_days: int | None = None
    expiry_date: date | None = None
    days_to_expiry: int | None = None


class WarehouseReportResponse(BaseModel):
    kind: str
    items: list[ReportRow]


class ScrapSettleRequest(BaseModel):
    scrap_weight: Decimal | None = Field(None, ge=0)
    scrap_assessed_value: Decimal | None = Field(None, ge=0)
    scrap_disposal_method: str | None = Field(None, max_length=50)
    scrap_recycler: str | None = Field(None, max_length=200)
    scrap_residual_value: Decimal | None = Field(None, ge=0)
    scrap_status: str | None = Field(None, max_length=16)


class OpeningImportError(BaseModel):
    row_no: int
    message: str


class OpeningImportResult(BaseModel):
    created_count: int
    line_count: int
    skipped_count: int
    documents: list[DocumentResponse] = []
    errors: list[OpeningImportError] = []


class QrPayloadResponse(BaseModel):
    id: int
    kind: str
    payload: str
    label: str
