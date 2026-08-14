"""Opening stock Excel template and import."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException, ErrorCode, ValidationError
from app.models.user import User
from app.models.warehouse import (
    CATEGORY_LABELS,
    CONDITION_LABELS,
    DEFAULT_LOCATION_CODE,
    SUPPLY_LABELS,
    InboundBusinessType,
    MaterialCategory,
    MaterialCondition,
    SupplyType,
    WarehouseLocation,
    WarehouseMaterial,
)
from app.services.warehouse.codes import material_identity_key
from app.services.warehouse.master import WarehouseMasterService
from app.services.warehouse.posting import WarehousePostingService, quantize_qty
from app.services.warehouse.queries import serialize_document

ENTRY_HEADERS = [
    "物资编码",
    "物资名称",
    "厂家",
    "规格",
    "单位",
    "类别",
    "供应",
    "成色",
    "库房编码",
    "库房名称",
    "货位编码",
    "货位名称",
    "项目编码",
    "项目名称",
    "数量",
    "日期",
    "经办人",
    "备注",
]

HEADER_ALIASES = {
    "物资编码": "material_code",
    "物资名称": "material_name",
    "厂家": "brand",
    "规格": "specification",
    "单位": "unit",
    "类别": "category",
    "供应": "supply_type",
    "成色": "condition",
    "库房编码": "warehouse_code",
    "库房名称": "warehouse_name",
    "货位编码": "location_code",
    "货位名称": "location_name",
    "项目编码": "project_code",
    "合同序号": "project_code",
    "项目名称": "project_name",
    "数量": "quantity",
    "日期": "occurred_on",
    "经办人": "handler",
    "备注": "description",
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)
REF_FILL = PatternFill("solid", fgColor="FFF2CC")


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _parse_quantity(value: Any) -> Decimal:
    raw = _cell_text(value).replace(",", "")
    if not raw:
        raise ValueError("数量不能为空")
    try:
        qty = quantize_qty(Decimal(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"数量无效: {raw}") from exc
    if qty <= 0:
        raise ValueError("数量必须大于零")
    return qty


def _parse_date(value: Any, fallback: date) -> date:
    if value in (None, ""):
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = _cell_text(value)
    if not raw:
        return fallback
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise ValueError(f"日期格式无效: {raw}，请使用 YYYY-MM-DD") from exc


CATEGORY_REVERSE = {label: item.value for item, label in CATEGORY_LABELS.items()}
SUPPLY_REVERSE = {label: item.value for item, label in SUPPLY_LABELS.items()}
CONDITION_REVERSE = {label: item.value for item, label in CONDITION_LABELS.items()}


def _resolve_enum(
    value: Any,
    reverse: dict,
    valid_values: tuple[str, ...],
    label: str,
) -> str:
    """Resolve a material enum field from its code (e.g. ZC) or label (e.g. 主材)."""
    raw = _cell_text(value)
    if not raw:
        raise ValueError(f"{label}不能为空")
    key = raw.casefold()
    for value_item in valid_values:
        if value_item.casefold() == key:
            return value_item
    for text, value_item in reverse.items():
        if text.casefold() == key:
            return value_item
    raise ValueError(f"{label}无效：{raw}")


def _autosize(sheet, min_width: int = 10, max_width: int = 28) -> None:
    for index, column in enumerate(sheet.columns, start=1):
        width = min_width
        for cell in column:
            value = "" if cell.value is None else str(cell.value)
            width = max(width, min(max_width, len(value) + 2))
        sheet.column_dimensions[get_column_letter(index)].width = width


def _style_header(sheet) -> None:
    for cell in sheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.row_dimensions[1].height = 22


class WarehouseOpeningService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.posting = WarehousePostingService(db, user)

    async def build_template(self) -> Workbook:
        warehouses, locations, projects, materials = await self._load_lookups()
        workbook = Workbook()

        guide = workbook.active
        assert guide is not None  # Workbook always has an active sheet
        guide.title = "填写说明"
        guide["A1"] = "期初材料录入表"
        guide["A1"].font = Font(bold=True, size=14)
        instructions = [
            "1. 只在「期初录入」工作表按行填写；对照表仅供复制编码，请勿改动表头。",
            "2. 必填：库房编码、项目编码（合同序号）、数量。",
            "3. 物资编码可空：填了则复用已有物资档案；留空则按本行物资名称、类别、供应、成色、单位、厂家、规格自动建档，重复自动复用。",
            "4. 物资编码留空时必填：物资名称、类别、供应、成色、单位；厂家、规格可空。",
            "5. 货位编码可空，空则入该库房的暂存区。",
            "6. 日期可空，空则按导入当天；经办人可空，空则按当前登录人。",
            "7. 导入后立即生成「期初」入库单并过账，同一库房/货位/项目/日期会合并为一张单。",
            "8. 有库存或单据的维度可以继续追加期初，请避免重复导入同一批数量。",
        ]
        for index, line in enumerate(instructions, start=3):
            guide[f"A{index}"] = line
        guide.column_dimensions["A"].width = 88

        entry = workbook.create_sheet("期初录入")
        entry.append(ENTRY_HEADERS)
        _style_header(entry)
        if materials and warehouses and projects:
            default_location = next(
                (
                    item
                    for item in locations
                    if item.warehouse_id == warehouses[0].id and item.is_default
                ),
                next(
                    (
                        item
                        for item in locations
                        if item.warehouse_id == warehouses[0].id
                    ),
                    None,
                ),
            )
            entry.append(
                [
                    materials[0].code,
                    materials[0].name,
                    materials[0].brand,
                    materials[0].specification,
                    materials[0].unit,
                    CATEGORY_LABELS.get(materials[0].category, materials[0].category),
                    SUPPLY_LABELS.get(
                        materials[0].supply_type, materials[0].supply_type
                    ),
                    CONDITION_LABELS.get(
                        materials[0].condition, materials[0].condition
                    ),
                    warehouses[0].code,
                    warehouses[0].name,
                    default_location.code
                    if default_location
                    else DEFAULT_LOCATION_CODE,
                    default_location.name if default_location else "暂存区",
                    projects[0].code,
                    projects[0].name,
                    None,
                    date.today().isoformat(),
                    self.user.full_name or self.user.username,
                    "",
                ]
            )
            for cell in entry[2]:
                cell.fill = REF_FILL
        _autosize(entry)

        material_sheet = workbook.create_sheet("物资对照")
        material_sheet.append(
            [
                "物资编码",
                "物资名称",
                "厂家",
                "规格",
                "单位",
                "类别",
                "供应",
                "成色",
                "状态",
            ]
        )
        _style_header(material_sheet)
        for item in materials:
            material_sheet.append(
                [
                    item.code,
                    item.name,
                    item.brand,
                    item.specification,
                    item.unit,
                    CATEGORY_LABELS.get(item.category, item.category),
                    SUPPLY_LABELS.get(item.supply_type, item.supply_type),
                    CONDITION_LABELS.get(item.condition, item.condition),
                    "启用" if item.is_active else "归档",
                ]
            )
        _autosize(material_sheet)

        location_sheet = workbook.create_sheet("库房货位对照")
        location_sheet.append(
            ["库房编码", "库房名称", "货位编码", "货位名称", "是否暂存/默认", "状态"]
        )
        _style_header(location_sheet)
        for location in locations:
            warehouse = location.warehouse
            location_sheet.append(
                [
                    warehouse.code if warehouse else "",
                    warehouse.name if warehouse else "",
                    location.code,
                    location.name,
                    "是" if location.is_default else "",
                    "启用" if location.is_active else "停用",
                ]
            )
        _autosize(location_sheet)

        project_sheet = workbook.create_sheet("项目对照")
        project_sheet.append(["项目编码", "项目名称", "甲方", "公司合同分类", "状态"])
        _style_header(project_sheet)
        for project in projects:
            project_sheet.append(
                [
                    project.code,
                    project.name,
                    getattr(project, "party_a_name", None) or "",
                    getattr(project, "company_category", None) or "",
                    "启用" if project.is_active else "停用",
                ]
            )
        _autosize(project_sheet)

        if materials:
            codes = ",".join(f'"{item.code}"' for item in materials[:50])
            validation = DataValidation(
                type="list", formula1=f"{codes}", allow_blank=True
            )
            validation.error = (
                "物资编码请从物资对照复制已有编码，或留空由系统按本行档案字段自动建档"
            )
            validation.errorTitle = "物资编码无效"
            entry.add_data_validation(validation)
            validation.add("A2:A2000")

        for sheet in workbook.worksheets:
            sheet.protection.sheet = False
            page_setup = sheet.sheet_properties.pageSetUpPr
            if page_setup is not None:
                page_setup.fitToPage = True
        return workbook

    async def import_workbook(
        self,
        content: bytes,
        filename: str | None = None,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        if not content:
            raise ValidationError(message="上传文件为空")
        try:
            workbook = load_workbook(BytesIO(content), data_only=True)
        except Exception as exc:
            raise ValidationError(
                message="无法读取 Excel，请使用系统下载的模板"
            ) from exc

        sheet = (
            workbook["期初录入"]
            if "期初录入" in workbook.sheetnames
            else workbook.active
        )
        assert sheet is not None  # loaded workbook always has an active sheet
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            raise ValidationError(message="Excel 中没有数据")

        header_map = self._header_map(rows[0])
        warehouses, locations, projects, materials = await self._load_lookups(
            include_inactive=True
        )
        material_by_code = {item.code.strip().casefold(): item for item in materials}
        material_by_identity = {item.identity_key: item for item in materials}
        warehouse_by_code = {item.code.strip().casefold(): item for item in warehouses}
        project_by_code = {item.code.strip().casefold(): item for item in projects}
        locations_by_key = {
            (item.warehouse_id, item.code.strip().casefold()): item
            for item in locations
        }
        default_location = {}
        for item in locations:
            if (
                item.is_default
                and item.warehouse_id not in default_location
                or item.warehouse_id not in default_location
                and item.code == DEFAULT_LOCATION_CODE
            ):
                default_location[item.warehouse_id] = item

        master = WarehouseMasterService(self.db, self.user)
        created_materials: dict[str, WarehouseMaterial] = {}
        errors: list[dict] = []
        grouped: dict[tuple, list[dict]] = defaultdict(list)
        today = date.today()
        default_handler = self.user.full_name or self.user.username or "期初导入"

        for offset, raw in enumerate(rows[1:], start=2):
            if raw is None or all(value in (None, "") for value in raw):
                continue
            payload = {
                field: raw[index] if index < len(raw) else None
                for field, index in header_map.items()
            }
            try:
                parsed = self._parse_row(
                    payload,
                    fallback_date=today,
                    fallback_handler=default_handler,
                    warehouse_by_code=warehouse_by_code,
                    project_by_code=project_by_code,
                    locations_by_key=locations_by_key,
                    default_location=default_location,
                )
            except ValueError as exc:
                errors.append({"row_no": offset, "message": str(exc)})
                continue
            try:
                material = await self._resolve_material(
                    parsed,
                    material_by_code=material_by_code,
                    material_by_identity=material_by_identity,
                    created_materials=created_materials,
                    master=master,
                )
            except ValueError as exc:
                errors.append({"row_no": offset, "message": str(exc)})
                continue
            parsed["material_id"] = material.id
            key = (
                parsed["warehouse_id"],
                parsed["location_id"],
                parsed["project_id"],
                parsed["occurred_on"],
                parsed["handler"],
            )
            grouped[key].append(parsed)

        if errors and not grouped:
            return {
                "created_count": 0,
                "line_count": 0,
                "skipped_count": len(errors),
                "documents": [],
                "errors": errors,
            }

        documents = []
        line_count = 0
        for (
            warehouse_id,
            location_id,
            project_id,
            occurred_on,
            handler,
        ), lines in grouped.items():
            document = await self.posting.post_inbound(
                warehouse_id=warehouse_id,
                location_id=location_id,
                project_id=project_id,
                occurred_on=occurred_on,
                handler=handler,
                business_type=InboundBusinessType.OPENING.value,
                reference_no=(filename or "期初材料录入表")[:100],
                description="期初材料录入表导入",
                lines=[
                    {
                        "material_id": line["material_id"],
                        "quantity": line["quantity"],
                        "description": line["description"],
                    }
                    for line in lines
                ],
                ip_address=ip_address,
                user_agent=user_agent,
            )
            documents.append(serialize_document(document))
            line_count += len(lines)

        return {
            "created_count": len(documents),
            "line_count": line_count,
            "skipped_count": len(errors),
            "documents": documents,
            "errors": errors,
        }

    def _header_map(self, header_row) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for index, value in enumerate(header_row or []):
            key = HEADER_ALIASES.get(_cell_text(value))
            if key:
                mapping[key] = index
        missing = [
            label
            for label, field in (
                ("物资编码", "material_code"),
                ("库房编码", "warehouse_code"),
                ("项目编码", "project_code"),
                ("数量", "quantity"),
            )
            if field not in mapping
        ]
        if missing:
            raise ValidationError(message=f"模板缺少列：{'、'.join(missing)}")
        return mapping

    def _parse_row(
        self,
        payload: dict,
        *,
        fallback_date: date,
        fallback_handler: str,
        warehouse_by_code: dict,
        project_by_code: dict,
        locations_by_key: dict,
        default_location: dict,
    ) -> dict:
        material_code = _cell_text(payload.get("material_code"))
        warehouse_code = _cell_text(payload.get("warehouse_code"))
        project_code = _cell_text(payload.get("project_code"))
        if not warehouse_code:
            raise ValueError("库房编码不能为空")
        if not project_code:
            raise ValueError("项目编码不能为空")

        material_profile = None
        if not material_code:
            name = _cell_text(payload.get("material_name"))
            if not name:
                raise ValueError("物资编码留空时，物资名称不能为空")
            unit = _cell_text(payload.get("unit"))
            if not unit:
                raise ValueError("物资编码留空时，单位不能为空")
            material_profile = {
                "name": name,
                "brand": _cell_text(payload.get("brand")),
                "specification": _cell_text(payload.get("specification")),
                "unit": unit,
                "category": _resolve_enum(
                    payload.get("category"),
                    CATEGORY_REVERSE,
                    tuple(item.value for item in MaterialCategory),
                    "类别",
                ),
                "supply_type": _resolve_enum(
                    payload.get("supply_type"),
                    SUPPLY_REVERSE,
                    tuple(item.value for item in SupplyType),
                    "供应",
                ),
                "condition": _resolve_enum(
                    payload.get("condition"),
                    CONDITION_REVERSE,
                    tuple(item.value for item in MaterialCondition),
                    "成色",
                ),
            }

        warehouse = warehouse_by_code.get(warehouse_code.casefold())
        if warehouse is None:
            raise ValueError(f"库房编码不存在：{warehouse_code}")
        if not warehouse.is_active:
            raise ValueError(f"库房已停用：{warehouse_code}")

        project = project_by_code.get(project_code.casefold())
        if project is None:
            raise ValueError(f"项目编码不存在：{project_code}")
        if not project.is_active:
            raise ValueError(f"项目已停用：{project_code}")

        location_code = _cell_text(payload.get("location_code"))
        if location_code:
            location = locations_by_key.get((warehouse.id, location_code.casefold()))
            if location is None:
                raise ValueError(f"库房 {warehouse_code} 下不存在货位 {location_code}")
        else:
            location = default_location.get(warehouse.id)
            if location is None:
                raise ValueError(
                    f"库房 {warehouse_code} 没有暂存区/默认货位，请填写货位编码"
                )
        if not location.is_active:
            raise ValueError(f"货位已停用：{location.code}")

        return {
            "material_code": material_code or None,
            "material_profile": material_profile,
            "warehouse_id": warehouse.id,
            "location_id": location.id,
            "project_id": project.id,
            "quantity": _parse_quantity(payload.get("quantity")),
            "occurred_on": _parse_date(payload.get("occurred_on"), fallback_date),
            "handler": _cell_text(payload.get("handler")) or fallback_handler,
            "description": _cell_text(payload.get("description")) or None,
        }

    async def _resolve_material(
        self,
        parsed: dict,
        *,
        material_by_code: dict,
        material_by_identity: dict,
        created_materials: dict,
        master: WarehouseMasterService,
    ) -> WarehouseMaterial:
        """Reuse an existing material (by code or identity) or auto-create its archive."""
        code = parsed.get("material_code")
        if code:
            material = material_by_code.get(code.casefold())
            if material is None:
                raise ValueError(f"物资编码不存在：{code}")
            if not material.is_active:
                raise ValueError(f"物资已归档，不能期初入库：{code}")
            return material

        profile = parsed["material_profile"]
        identity = material_identity_key(
            profile["name"],
            profile["brand"],
            profile["specification"],
            profile["unit"],
            profile["condition"],
            profile["supply_type"],
        )
        cached = created_materials.get(identity)
        if cached:
            return cached
        existing = material_by_identity.get(identity)
        if existing is not None:
            if not existing.is_active:
                raise ValueError(f"物资已归档，不能期初入库：{existing.code}")
            return existing

        try:
            material = await master.create_material(
                {
                    "category": MaterialCategory(profile["category"]),
                    "supply_type": SupplyType(profile["supply_type"]),
                    "condition": MaterialCondition(profile["condition"]),
                    "name": profile["name"],
                    "brand": profile["brand"],
                    "specification": profile["specification"],
                    "unit": profile["unit"],
                    "minimum_stock": Decimal(0),
                }
            )
        except AppException as exc:
            if exc.error_code != ErrorCode.MATERIAL_DUPLICATE:
                raise
            refreshed = await self.db.execute(
                select(WarehouseMaterial).where(
                    WarehouseMaterial.identity_key == identity
                )
            )
            material = refreshed.scalar_one_or_none()
            if material is None:
                raise ValueError("物资建档失败，请重试") from exc
            if not material.is_active:
                raise ValueError(f"物资已归档，不能期初入库：{material.code}") from exc

        created_materials[identity] = material
        material_by_identity[identity] = material
        material_by_code[material.code.strip().casefold()] = material
        return material

    async def _load_lookups(self, *, include_inactive: bool = False):
        master = WarehouseMasterService(self.db, self.user)
        warehouses = await master.list_warehouses(include_inactive=include_inactive)
        projects = await master.list_projects(include_inactive=include_inactive)
        materials = await master.list_materials(
            include_inactive=include_inactive, limit=10000
        )
        query = select(WarehouseLocation).options(
            selectinload(WarehouseLocation.warehouse)
        )
        if not include_inactive:
            query = query.where(WarehouseLocation.is_active.is_(True))
        locations = list((await self.db.execute(query)).scalars().unique().all())
        return warehouses, locations, projects, materials
