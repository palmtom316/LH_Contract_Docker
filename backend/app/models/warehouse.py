"""Warehouse management models."""

from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MaterialCategory(str, enum.Enum):
    ZC = "ZC"
    FC = "FC"
    GJ = "GJ"
    LB = "LB"


class SupplyType(str, enum.Enum):
    J = "J"
    Y = "Y"


class MaterialCondition(str, enum.Enum):
    NEW = "NEW"
    SCRAP = "SCRAP"


class DocumentType(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    TRANSFER = "TRANSFER"
    COUNT_ADJUSTMENT = "COUNT_ADJUSTMENT"
    REVERSAL = "REVERSAL"


class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOIDED = "VOIDED"


class InboundBusinessType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    OWNER_SUPPLY = "OWNER_SUPPLY"
    RETURN = "RETURN"
    DEMOLITION = "DEMOLITION"
    OPENING = "OPENING"
    COUNT_GAIN = "COUNT_GAIN"


class OutboundBusinessType(str, enum.Enum):
    ISSUE = "ISSUE"
    SCRAP_RETURN = "SCRAP_RETURN"
    WRITE_OFF = "WRITE_OFF"
    SCRAP_DISPOSAL = "SCRAP_DISPOSAL"
    COUNT_LOSS = "COUNT_LOSS"


class CountStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ENTERED = "ENTERED"
    REVIEWED = "REVIEWED"
    CONFIRMED = "CONFIRMED"
    VOIDED = "VOIDED"


class PeriodStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ScrapDisposalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    WEIGHED = "WEIGHED"
    SETTLED = "SETTLED"
    VOIDED = "VOIDED"


CATEGORY_LABELS = {
    MaterialCategory.ZC: "主材",
    MaterialCategory.FC: "辅材",
    MaterialCategory.GJ: "工器具",
    MaterialCategory.LB: "劳保",
}

SUPPLY_LABELS = {
    SupplyType.J: "甲供",
    SupplyType.Y: "乙供",
}

CONDITION_LABELS = {
    MaterialCondition.NEW: "新料",
    MaterialCondition.SCRAP: "废旧回收",
}

SUPPLY_CONDITION_SEGMENT = {
    (SupplyType.J, MaterialCondition.NEW): "J",
    (SupplyType.Y, MaterialCondition.NEW): "Y",
    (SupplyType.J, MaterialCondition.SCRAP): "JF",
    (SupplyType.Y, MaterialCondition.SCRAP): "YF",
}

DOCUMENT_NO_PREFIX = {
    DocumentType.INBOUND: "IN",
    DocumentType.OUTBOUND: "OUT",
    DocumentType.TRANSFER: "TR",
    DocumentType.COUNT_ADJUSTMENT: "CNT",
    DocumentType.REVERSAL: "REV",
}

DEFAULT_LOCATION_CODE = "STAGING"
DEFAULT_LOCATION_NAME = "暂存区"


class Warehouse(Base):
    __tablename__ = "warehouse_warehouses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    manager_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    locations = relationship(
        "WarehouseLocation",
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )
    scopes = relationship(
        "WarehouseUserScope",
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )


class WarehouseLocation(Base):
    __tablename__ = "warehouse_locations"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "code", name="uq_warehouse_location_code"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(
        Integer,
        ForeignKey("warehouse_warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    warehouse = relationship("Warehouse", back_populates="locations")


class WarehouseProject(Base):
    __tablename__ = "warehouse_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    upstream_contract_id = Column(
        Integer, ForeignKey("contracts_upstream.id"), nullable=True, index=True
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WarehouseMaterial(Base):
    __tablename__ = "warehouse_materials"
    __table_args__ = (
        UniqueConstraint("identity_key", name="uq_warehouse_material_identity"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    legacy_code = Column(String(50), nullable=True, index=True)
    category = Column(String(8), nullable=False, index=True)
    supply_type = Column(String(8), nullable=False, index=True)
    condition = Column(String(16), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    brand = Column(String(100), nullable=False, default="")
    specification = Column(String(200), nullable=False, default="")
    unit = Column(String(20), nullable=False)
    quantity_scale = Column(Integer, nullable=False, default=3)
    tracks_batch = Column(Boolean, nullable=False, default=False)
    tracks_serial = Column(Boolean, nullable=False, default=False)
    shelf_life_days = Column(Integer, nullable=True)
    minimum_stock = Column(Numeric(18, 4), nullable=False, default=0)
    description = Column(Text, nullable=True)
    identity_key = Column(String(64), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WarehouseCodeCounter(Base):
    __tablename__ = "warehouse_code_counters"

    category = Column(String(8), primary_key=True)
    supply_condition = Column(String(8), primary_key=True)
    next_number = Column(Integer, nullable=False, default=1)


class WarehouseDocumentCounter(Base):
    __tablename__ = "warehouse_document_counters"

    prefix = Column(String(8), primary_key=True)
    occurred_on = Column(Date, primary_key=True)
    next_number = Column(Integer, nullable=False, default=1)


class WarehouseUserScope(Base):
    __tablename__ = "warehouse_user_scopes"
    __table_args__ = (
        UniqueConstraint("user_id", "warehouse_id", name="uq_warehouse_user_scope"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id = Column(
        Integer,
        ForeignKey("warehouse_warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    warehouse = relationship("Warehouse", back_populates="scopes")


class WarehouseDocument(Base):
    __tablename__ = "warehouse_documents"
    __table_args__ = (
        UniqueConstraint(
            "created_by", "idempotency_key", name="uq_warehouse_document_idempotency"
        ),
        UniqueConstraint(
            "reversed_document_id", name="uq_warehouse_document_reversed_document"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_no = Column(String(40), unique=True, nullable=False, index=True)
    document_type = Column(String(32), nullable=False, index=True)
    status = Column(
        String(16), nullable=False, default=DocumentStatus.POSTED.value, index=True
    )
    occurred_on = Column(Date, nullable=False, index=True)
    business_type = Column(String(32), nullable=True, index=True)
    reference_no = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    handler = Column(String(100), nullable=False)
    idempotency_key = Column(String(80), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    voided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(Text, nullable=True)
    delivery_note_file = Column(String(500), nullable=True)
    delivery_note_file_name = Column(String(255), nullable=True)
    scrap_basis_file = Column(String(500), nullable=True)
    scrap_basis_file_name = Column(String(255), nullable=True)
    supplier_name = Column(String(200), nullable=True)
    purchase_order_no = Column(String(100), nullable=True)
    delivery_note_no = Column(String(100), nullable=True)
    acceptance_no = Column(String(100), nullable=True)
    acceptor = Column(String(100), nullable=True)
    qc_result = Column(String(50), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    batch_no = Column(String(100), nullable=True)
    requisition_no = Column(String(100), nullable=True)
    work_package = Column(String(200), nullable=True)
    crew_name = Column(String(100), nullable=True)
    requester_name = Column(String(100), nullable=True)
    receiver_name = Column(String(100), nullable=True)
    signed_off = Column(Boolean, nullable=False, default=False)
    scrap_status = Column(String(16), nullable=True, index=True)
    scrap_weight = Column(Numeric(18, 4), nullable=True)
    scrap_assessed_value = Column(Numeric(18, 2), nullable=True)
    scrap_disposal_method = Column(String(50), nullable=True)
    scrap_recycler = Column(String(200), nullable=True)
    scrap_residual_value = Column(Numeric(18, 2), nullable=True)
    scrap_settled_at = Column(DateTime(timezone=True), nullable=True)
    scrap_settled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reversed_document_id = Column(
        Integer, ForeignKey("warehouse_documents.id"), nullable=True, index=True
    )

    lines = relationship(
        "WarehouseDocumentLine",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="WarehouseDocumentLine.line_no",
    )
    ledger_entries = relationship(
        "WarehouseLedgerEntry",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    supplements = relationship(
        "WarehouseBusinessSupplement",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class WarehouseDocumentLine(Base):
    __tablename__ = "warehouse_document_lines"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "line_no", name="uq_warehouse_document_line_no"
        ),
        CheckConstraint("quantity > 0", name="ck_warehouse_document_line_qty_positive"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("warehouse_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_no = Column(Integer, nullable=False)
    material_id = Column(
        Integer, ForeignKey("warehouse_materials.id"), nullable=False, index=True
    )
    quantity = Column(Numeric(18, 4), nullable=False)
    source_warehouse_id = Column(
        Integer, ForeignKey("warehouse_warehouses.id"), nullable=True
    )
    source_location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=True
    )
    source_project_id = Column(
        Integer, ForeignKey("warehouse_projects.id"), nullable=True
    )
    target_warehouse_id = Column(
        Integer, ForeignKey("warehouse_warehouses.id"), nullable=True
    )
    target_location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=True
    )
    target_project_id = Column(
        Integer, ForeignKey("warehouse_projects.id"), nullable=True
    )
    original_document_line_id = Column(
        Integer, ForeignKey("warehouse_document_lines.id"), nullable=True
    )
    batch_no = Column(String(100), nullable=False, default="", index=True)
    serial_no = Column(String(100), nullable=False, default="", index=True)
    heat_no = Column(String(100), nullable=True)
    production_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)

    document = relationship("WarehouseDocument", back_populates="lines")
    material = relationship("WarehouseMaterial")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    source_location = relationship(
        "WarehouseLocation", foreign_keys=[source_location_id]
    )
    source_project = relationship("WarehouseProject", foreign_keys=[source_project_id])
    target_warehouse = relationship("Warehouse", foreign_keys=[target_warehouse_id])
    target_location = relationship(
        "WarehouseLocation", foreign_keys=[target_location_id]
    )
    target_project = relationship("WarehouseProject", foreign_keys=[target_project_id])


class WarehouseLedgerEntry(Base):
    __tablename__ = "warehouse_ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "document_line_id",
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
            "batch_no",
            "serial_no",
            name="uq_warehouse_ledger_line_dimension",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("warehouse_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_line_id = Column(
        Integer,
        ForeignKey("warehouse_document_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    warehouse_id = Column(
        Integer, ForeignKey("warehouse_warehouses.id"), nullable=False, index=True
    )
    location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=False, index=True
    )
    project_id = Column(
        Integer, ForeignKey("warehouse_projects.id"), nullable=False, index=True
    )
    material_id = Column(
        Integer, ForeignKey("warehouse_materials.id"), nullable=False, index=True
    )
    batch_no = Column(String(100), nullable=False, default="", index=True)
    serial_no = Column(String(100), nullable=False, default="", index=True)
    expiry_date = Column(Date, nullable=True, index=True)
    quantity_delta = Column(Numeric(18, 4), nullable=False)
    occurred_on = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("WarehouseDocument", back_populates="ledger_entries")
    document_line = relationship("WarehouseDocumentLine")
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    project = relationship("WarehouseProject")
    material = relationship("WarehouseMaterial")


class WarehouseStockBalance(Base):
    __tablename__ = "warehouse_stock_balances"
    __table_args__ = (
        UniqueConstraint(
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
            "batch_no",
            "serial_no",
            name="uq_warehouse_stock_dimension",
        ),
        CheckConstraint("quantity >= 0", name="ck_warehouse_stock_non_negative"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(
        Integer, ForeignKey("warehouse_warehouses.id"), nullable=False, index=True
    )
    location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=False, index=True
    )
    project_id = Column(
        Integer, ForeignKey("warehouse_projects.id"), nullable=False, index=True
    )
    material_id = Column(
        Integer, ForeignKey("warehouse_materials.id"), nullable=False, index=True
    )
    batch_no = Column(String(100), nullable=False, default="", index=True)
    serial_no = Column(String(100), nullable=False, default="", index=True)
    expiry_date = Column(Date, nullable=True, index=True)
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    project = relationship("WarehouseProject")
    material = relationship("WarehouseMaterial")


class WarehouseCount(Base):
    __tablename__ = "warehouse_counts"
    __table_args__ = (
        UniqueConstraint(
            "created_by", "idempotency_key", name="uq_warehouse_count_idempotency"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    count_no = Column(String(40), unique=True, nullable=False, index=True)
    warehouse_id = Column(
        Integer, ForeignKey("warehouse_warehouses.id"), nullable=False, index=True
    )
    location_id = Column(Integer, ForeignKey("warehouse_locations.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("warehouse_projects.id"), nullable=True)
    counted_on = Column(Date, nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=True)
    snapshot_source = Column(String(32), nullable=False, default="stock_balances")
    status = Column(
        String(16), nullable=False, default=CountStatus.DRAFT.value, index=True
    )
    description = Column(Text, nullable=True)
    void_reason = Column(Text, nullable=True)
    review_notes = Column(Text, nullable=True)
    idempotency_key = Column(String(80), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    voided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    reopened_from_id = Column(
        Integer, ForeignKey("warehouse_counts.id"), nullable=True
    )
    adjustment_document_id = Column(
        Integer, ForeignKey("warehouse_documents.id"), nullable=True
    )

    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    project = relationship("WarehouseProject")
    lines = relationship(
        "WarehouseCountLine",
        back_populates="count",
        cascade="all, delete-orphan",
    )


class WarehouseCountLine(Base):
    __tablename__ = "warehouse_count_lines"
    __table_args__ = (
        UniqueConstraint(
            "count_id",
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
            "batch_no",
            "serial_no",
            name="uq_warehouse_count_line_dimension",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    count_id = Column(
        Integer,
        ForeignKey("warehouse_counts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    warehouse_id = Column(
        Integer, ForeignKey("warehouse_warehouses.id"), nullable=False
    )
    location_id = Column(Integer, ForeignKey("warehouse_locations.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("warehouse_projects.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("warehouse_materials.id"), nullable=False)
    batch_no = Column(String(100), nullable=False, default="")
    serial_no = Column(String(100), nullable=False, default="")
    expiry_date = Column(Date, nullable=True)
    book_quantity = Column(Numeric(18, 4), nullable=False)
    counted_quantity = Column(Numeric(18, 4), nullable=True)
    variance_reviewed = Column(Boolean, nullable=False, default=False)
    variance_note = Column(Text, nullable=True)
    adjustment_document_id = Column(
        Integer, ForeignKey("warehouse_documents.id"), nullable=True
    )

    count = relationship("WarehouseCount", back_populates="lines")
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    project = relationship("WarehouseProject")
    material = relationship("WarehouseMaterial")


class WarehouseBusinessSupplement(Base):
    __tablename__ = "warehouse_business_supplements"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "line_key",
            name="uq_warehouse_supplement_document_line",
        ),
        CheckConstraint(
            "unit_price IS NULL OR unit_price >= 0",
            name="ck_warehouse_supplement_unit_price_non_negative",
        ),
        CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="ck_warehouse_supplement_amount_non_negative",
        ),
        CheckConstraint(
            "weigh_in IS NULL OR weigh_in >= 0",
            name="ck_warehouse_supplement_weigh_in_non_negative",
        ),
        CheckConstraint(
            "residual_value IS NULL OR residual_value >= 0",
            name="ck_warehouse_supplement_residual_non_negative",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("warehouse_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_line_id = Column(
        Integer, ForeignKey("warehouse_document_lines.id"), nullable=True, index=True
    )
    line_key = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    delivery_note_no = Column(String(100), nullable=True)
    acceptance_no = Column(String(100), nullable=True)
    contract_no = Column(String(100), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    price_type = Column(String(50), nullable=True)
    unit_price = Column(Numeric(18, 4), nullable=True)
    amount = Column(Numeric(18, 2), nullable=True)
    weigh_in = Column(Numeric(18, 4), nullable=True)
    residual_value = Column(Numeric(18, 2), nullable=True)
    admin_notes = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    document = relationship("WarehouseDocument", back_populates="supplements")
    document_line = relationship("WarehouseDocumentLine")
    histories = relationship(
        "WarehouseBusinessSupplementHistory",
        back_populates="supplement",
        cascade="all, delete-orphan",
        order_by="WarehouseBusinessSupplementHistory.version",
    )


class WarehouseBusinessSupplementHistory(Base):
    __tablename__ = "warehouse_business_supplement_histories"
    __table_args__ = (
        UniqueConstraint(
            "supplement_id",
            "version",
            name="uq_warehouse_supplement_history_version",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplement_id = Column(
        Integer,
        ForeignKey("warehouse_business_supplements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = Column(
        Integer, ForeignKey("warehouse_documents.id"), nullable=False, index=True
    )
    document_line_id = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False)
    payload = Column(Text, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    supplement = relationship(
        "WarehouseBusinessSupplement", back_populates="histories"
    )


class WarehousePeriod(Base):
    __tablename__ = "warehouse_periods"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_warehouse_period_year_month"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_warehouse_period_month"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)
    status = Column(
        String(16), nullable=False, default=PeriodStatus.OPEN.value, index=True
    )
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    reopened_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reopened_at = Column(DateTime(timezone=True), nullable=True)
    reopen_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WarehouseBalanceRepair(Base):
    __tablename__ = "warehouse_balance_repairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dry_run = Column(Boolean, nullable=False, default=True)
    repaired = Column(Boolean, nullable=False, default=False)
    reason = Column(Text, nullable=True)
    dimensions = Column(Integer, nullable=False, default=0)
    mismatches = Column(Integer, nullable=False, default=0)
    differences = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WarehouseUnit(Base):
    __tablename__ = "warehouse_units"
    __table_args__ = (
        UniqueConstraint("code", name="uq_warehouse_unit_code"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    aliases = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversions_from = relationship(
        "WarehouseUnitConversion",
        foreign_keys="WarehouseUnitConversion.from_unit_id",
        back_populates="from_unit",
        cascade="all, delete-orphan",
    )


class WarehouseUnitConversion(Base):
    __tablename__ = "warehouse_unit_conversions"
    __table_args__ = (
        UniqueConstraint(
            "from_unit_id", "to_unit_id", name="uq_warehouse_unit_conversion"
        ),
        CheckConstraint("factor > 0", name="ck_warehouse_unit_conversion_factor"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_unit_id = Column(
        Integer, ForeignKey("warehouse_units.id", ondelete="CASCADE"), nullable=False
    )
    to_unit_id = Column(
        Integer, ForeignKey("warehouse_units.id", ondelete="CASCADE"), nullable=False
    )
    factor = Column(Numeric(18, 6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    from_unit = relationship(
        "WarehouseUnit", foreign_keys=[from_unit_id], back_populates="conversions_from"
    )
    to_unit = relationship("WarehouseUnit", foreign_keys=[to_unit_id])
