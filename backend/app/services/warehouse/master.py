"""Warehouse master-data services."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import (
    AppException,
    DuplicateRecordError,
    ErrorCode,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.contract_upstream import ContractUpstream
from app.models.user import User
from app.models.warehouse import (
    DEFAULT_LOCATION_CODE,
    DEFAULT_LOCATION_NAME,
    Warehouse,
    WarehouseCount,
    WarehouseCountLine,
    WarehouseDocumentLine,
    WarehouseLocation,
    WarehouseMaterial,
    WarehouseProject,
    WarehouseStockBalance,
)
from app.services.audit_service import AuditAction, ResourceType, create_audit_log
from app.services.warehouse.codes import generate_material_code, material_identity_key


class WarehouseMasterService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def list_warehouses(
        self, *, include_inactive: bool = False
    ) -> list[Warehouse]:
        query = (
            select(Warehouse)
            .options(selectinload(Warehouse.locations))
            .order_by(Warehouse.code)
        )
        if not include_inactive:
            query = query.where(Warehouse.is_active.is_(True))
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def create_warehouse(self, data: dict) -> Warehouse:
        await self._assert_unique_warehouse(data["code"], data["name"])
        warehouse = Warehouse(
            code=data["code"].strip(),
            name=data["name"].strip(),
            address=data.get("address"),
            manager_name=data.get("manager_name"),
            is_active=data.get("is_active", True),
            created_by=self.user.id,
        )
        self.db.add(warehouse)
        await self.db.flush()
        staging = WarehouseLocation(
            warehouse_id=warehouse.id,
            code=DEFAULT_LOCATION_CODE,
            name=DEFAULT_LOCATION_NAME,
            is_default=True,
            is_active=True,
            created_by=self.user.id,
        )
        self.db.add(staging)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.CREATE,
            ResourceType.WAREHOUSE,
            resource_id=warehouse.id,
            resource_name=warehouse.name,
            new_values={"code": warehouse.code, "name": warehouse.name},
        )
        return await self.get_warehouse(warehouse.id)

    async def update_warehouse(self, warehouse_id: int, data: dict) -> Warehouse:
        warehouse = await self.get_warehouse(warehouse_id)
        if "name" in data and data["name"] and data["name"] != warehouse.name:
            await self._assert_unique_warehouse(
                warehouse.code, data["name"], exclude_id=warehouse.id
            )
            warehouse.name = data["name"].strip()
        if "address" in data:
            warehouse.address = data["address"]
        if "manager_name" in data:
            warehouse.manager_name = data["manager_name"]
        if "is_active" in data and data["is_active"] is not None:
            if data["is_active"]:
                has_default = any(
                    loc.is_default and loc.is_active for loc in warehouse.locations
                )
                if not has_default:
                    raise ValidationError(message="启用库房前必须至少有一个暂存区货位")
            warehouse.is_active = data["is_active"]
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE,
            ResourceType.WAREHOUSE,
            resource_id=warehouse.id,
            resource_name=warehouse.name,
            new_values=data,
        )
        return await self.get_warehouse(warehouse.id)

    async def delete_warehouse(self, warehouse_id: int) -> None:
        warehouse = await self.get_warehouse(warehouse_id)
        await self._assert_warehouse_unused(warehouse_id)
        await self.db.delete(warehouse)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.DELETE,
            ResourceType.WAREHOUSE,
            resource_id=warehouse.id,
            resource_name=warehouse.name,
            old_values={"code": warehouse.code, "name": warehouse.name},
        )

    async def get_warehouse(self, warehouse_id: int) -> Warehouse:
        result = await self.db.execute(
            select(Warehouse)
            .options(selectinload(Warehouse.locations))
            .where(Warehouse.id == warehouse_id)
        )
        warehouse = result.scalar_one_or_none()
        if warehouse is None:
            raise ResourceNotFoundError(resource_type="库房", resource_id=warehouse_id)
        return warehouse

    async def create_location(self, warehouse_id: int, data: dict) -> WarehouseLocation:
        warehouse = await self.get_warehouse(warehouse_id)
        result = await self.db.execute(
            select(WarehouseLocation).where(
                WarehouseLocation.warehouse_id == warehouse_id,
                WarehouseLocation.code == data["code"].strip(),
            )
        )
        if result.scalar_one_or_none():
            raise DuplicateRecordError(
                resource_type="货位", field_name="编码", field_value=data["code"]
            )
        if data.get("is_default"):
            await self._clear_default_location(warehouse_id)
        location = WarehouseLocation(
            warehouse_id=warehouse.id,
            code=data["code"].strip(),
            name=data["name"].strip(),
            description=data.get("description"),
            is_default=bool(data.get("is_default")),
            is_active=data.get("is_active", True),
            created_by=self.user.id,
        )
        self.db.add(location)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.CREATE,
            ResourceType.WAREHOUSE_LOCATION,
            resource_id=location.id,
            resource_name=location.name,
            new_values={"warehouse_id": warehouse_id, "code": location.code},
        )
        return location

    async def get_location(self, location_id: int) -> WarehouseLocation:
        location = await self.db.get(WarehouseLocation, location_id)
        if location is None:
            raise ResourceNotFoundError(resource_type="货位", resource_id=location_id)
        return location

    async def update_location(self, location_id: int, data: dict) -> WarehouseLocation:
        location = await self.db.get(WarehouseLocation, location_id)
        if location is None:
            raise ResourceNotFoundError(resource_type="货位", resource_id=location_id)
        if data.get("name"):
            location.name = data["name"].strip()
        if "description" in data:
            location.description = data["description"]
        if data.get("is_default"):
            await self._clear_default_location(location.warehouse_id)
            location.is_default = True
        elif "is_default" in data and data["is_default"] is False:
            location.is_default = False
        if "is_active" in data and data["is_active"] is not None:
            location.is_active = data["is_active"]
        await self.db.flush()
        return location

    async def delete_location(self, location_id: int) -> None:
        location = await self.get_location(location_id)
        warehouse = await self.get_warehouse(location.warehouse_id)
        active_locations = [
            item
            for item in warehouse.locations
            if item.is_active and item.id != location.id
        ]
        if warehouse.is_active and not active_locations:
            raise ValidationError(message="启用中的库房至少保留一个货位")
        if location.is_default and warehouse.is_active:
            raise ValidationError(
                message="暂存区是库房默认货位，请先指定其他默认货位后再删除"
            )
        await self._assert_location_unused(location.id)
        await self.db.delete(location)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.DELETE,
            ResourceType.WAREHOUSE_LOCATION,
            resource_id=location.id,
            resource_name=location.name,
            old_values={"warehouse_id": location.warehouse_id, "code": location.code},
        )

    async def list_projects(
        self, *, include_inactive: bool = False, q: str | None = None
    ):
        query = (
            select(WarehouseProject, ContractUpstream)
            .outerjoin(
                ContractUpstream,
                WarehouseProject.upstream_contract_id == ContractUpstream.id,
            )
            .order_by(WarehouseProject.code)
        )
        if not include_inactive:
            query = query.where(WarehouseProject.is_active.is_(True))
        if q:
            like = f"%{q.strip()}%"
            query = query.where(
                or_(
                    WarehouseProject.code.ilike(like),
                    WarehouseProject.name.ilike(like),
                    ContractUpstream.contract_name.ilike(like),
                    ContractUpstream.party_a_name.ilike(like),
                )
            )
        result = await self.db.execute(query)
        return [
            self._with_contract_fields(project, contract)
            for project, contract in result.all()
        ]

    async def lookup_upstream_contracts(
        self,
        *,
        q: str | None = None,
        serial_number: int | None = None,
        limit: int = 20,
    ) -> list[ContractUpstream]:
        query = select(ContractUpstream)
        if serial_number is not None:
            query = query.where(ContractUpstream.serial_number == serial_number)
        elif q:
            raw = q.strip()
            if raw.isdigit():
                query = query.where(
                    or_(
                        ContractUpstream.serial_number == int(raw),
                        ContractUpstream.contract_name.ilike(f"%{raw}%"),
                    )
                )
            else:
                query = query.where(ContractUpstream.contract_name.ilike(f"%{raw}%"))
        else:
            return []
        result = await self.db.execute(
            query.order_by(ContractUpstream.serial_number.asc().nulls_last()).limit(
                limit
            )
        )
        return list(result.scalars().all())

    async def create_project(self, data: dict) -> WarehouseProject:
        contract = await self._resolve_upstream_contract(data)
        if contract is None:
            raise ValidationError(
                message="请输入有效的上游合同序号，或从合同名称中选择一份合同"
            )
        code = (
            str(contract.serial_number)
            if contract.serial_number is not None
            else str(contract.id)
        )
        result = await self.db.execute(
            select(WarehouseProject).where(WarehouseProject.code == code)
        )
        if result.scalar_one_or_none():
            raise DuplicateRecordError(
                resource_type="项目", field_name="合同序号", field_value=code
            )
        project = WarehouseProject(
            code=code,
            name=contract.contract_name,
            upstream_contract_id=contract.id,
            is_active=data.get("is_active", True),
            created_by=self.user.id,
        )
        self.db.add(project)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.CREATE,
            ResourceType.WAREHOUSE_PROJECT,
            resource_id=project.id,
            resource_name=project.name,
            new_values={"code": project.code, "upstream_contract_id": contract.id},
        )
        return await self.get_project(project.id)

    async def update_project(self, project_id: int, data: dict) -> WarehouseProject:
        project = await self.db.get(WarehouseProject, project_id)
        if project is None:
            raise ResourceNotFoundError(resource_type="项目", resource_id=project_id)
        if data.get("upstream_contract_id"):
            contract = await self._resolve_upstream_contract(data)
            if contract is None:
                raise ValidationError(message="未找到对应的上游合同")
            project.upstream_contract_id = contract.id
            if contract.serial_number is not None:
                project.code = str(contract.serial_number)
            project.name = contract.contract_name
        elif data.get("name"):
            project.name = data["name"].strip()
        if "is_active" in data and data["is_active"] is not None:
            project.is_active = data["is_active"]
        await self.db.flush()
        return await self.get_project(project.id)

    async def get_project(self, project_id: int) -> WarehouseProject:
        result = await self.db.execute(
            select(WarehouseProject, ContractUpstream)
            .outerjoin(
                ContractUpstream,
                WarehouseProject.upstream_contract_id == ContractUpstream.id,
            )
            .where(WarehouseProject.id == project_id)
        )
        row = result.first()
        if row is None:
            raise ResourceNotFoundError(resource_type="项目", resource_id=project_id)
        return self._with_contract_fields(row[0], row[1])

    async def _resolve_upstream_contract(self, data: dict) -> ContractUpstream | None:
        contract_id = data.get("upstream_contract_id")
        if contract_id:
            contract = await self.db.get(ContractUpstream, contract_id)
            if contract is None:
                raise ResourceNotFoundError(
                    resource_type="上游合同", resource_id=contract_id
                )
            return contract
        code = str(data.get("code") or "").strip()
        if code.isdigit():
            result = await self.db.execute(
                select(ContractUpstream).where(
                    ContractUpstream.serial_number == int(code)
                )
            )
            return result.scalar_one_or_none()
        return None

    @staticmethod
    def _with_contract_fields(
        project: WarehouseProject, contract: ContractUpstream | None
    ) -> WarehouseProject:
        project.company_category = contract.company_category if contract else None
        project.party_a_name = contract.party_a_name if contract else None
        if contract:
            if contract.serial_number is not None:
                project.code = str(contract.serial_number)
            project.name = contract.contract_name
        return project

    async def list_materials(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        supply_type: str | None = None,
        condition: str | None = None,
        include_inactive: bool = False,
        limit: int = 50,
    ) -> list[WarehouseMaterial]:
        query = select(WarehouseMaterial).order_by(WarehouseMaterial.code)
        if not include_inactive:
            query = query.where(WarehouseMaterial.is_active.is_(True))
        if category:
            query = query.where(WarehouseMaterial.category == category)
        if supply_type:
            query = query.where(WarehouseMaterial.supply_type == supply_type)
        if condition:
            query = query.where(WarehouseMaterial.condition == condition)
        if q:
            like = f"%{q.strip()}%"
            query = query.where(
                or_(
                    WarehouseMaterial.code.ilike(like),
                    WarehouseMaterial.legacy_code.ilike(like),
                    WarehouseMaterial.name.ilike(like),
                    WarehouseMaterial.brand.ilike(like),
                    WarehouseMaterial.specification.ilike(like),
                )
            )
        result = await self.db.execute(query.limit(limit))
        return list(result.scalars().all())

    async def create_material(self, data: dict) -> WarehouseMaterial:
        identity = material_identity_key(
            data["name"],
            data.get("brand") or "",
            data.get("specification") or "",
            data["unit"],
            data["condition"],
            data["supply_type"],
        )
        existing = await self.db.execute(
            select(WarehouseMaterial).where(WarehouseMaterial.identity_key == identity)
        )
        if existing.scalar_one_or_none():
            raise AppException(
                error_code=ErrorCode.MATERIAL_DUPLICATE,
                message="已存在相同名称、厂家、规格、单位、成色和供应方式的物资",
                status_code=409,
            )
        code = await generate_material_code(
            self.db, data["category"], data["supply_type"], data["condition"]
        )
        material = WarehouseMaterial(
            code=code,
            legacy_code=data.get("legacy_code"),
            category=data["category"].value
            if hasattr(data["category"], "value")
            else data["category"],
            supply_type=data["supply_type"].value
            if hasattr(data["supply_type"], "value")
            else data["supply_type"],
            condition=data["condition"].value
            if hasattr(data["condition"], "value")
            else data["condition"],
            name=data["name"].strip(),
            brand=(data.get("brand") or "").strip(),
            specification=(data.get("specification") or "").strip(),
            unit=data["unit"].strip(),
            minimum_stock=data.get("minimum_stock") or 0,
            description=data.get("description"),
            identity_key=identity,
            is_active=True,
            created_by=self.user.id,
            updated_by=self.user.id,
        )
        self.db.add(material)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.CREATE,
            ResourceType.WAREHOUSE_MATERIAL,
            resource_id=material.id,
            resource_name=material.code,
            new_values={"code": material.code, "name": material.name},
        )
        return material

    async def update_material(self, material_id: int, data: dict) -> WarehouseMaterial:
        material = await self.get_material(material_id)
        name = data.get("name", material.name)
        brand = data["brand"] if "brand" in data else material.brand
        specification = (
            data["specification"] if "specification" in data else material.specification
        )
        unit = data.get("unit", material.unit)
        identity = material_identity_key(
            name,
            brand or "",
            specification or "",
            unit,
            material.condition,
            material.supply_type,
        )
        if identity != material.identity_key:
            existing = await self.db.execute(
                select(WarehouseMaterial).where(
                    WarehouseMaterial.identity_key == identity,
                    WarehouseMaterial.id != material.id,
                )
            )
            if existing.scalar_one_or_none():
                raise AppException(
                    error_code=ErrorCode.MATERIAL_DUPLICATE,
                    message="已存在相同名称、厂家、规格、单位、成色和供应方式的物资",
                    status_code=409,
                )
            material.identity_key = identity
        if data.get("name"):
            material.name = data["name"].strip()
        if "brand" in data:
            material.brand = (data["brand"] or "").strip()
        if "specification" in data:
            material.specification = (data["specification"] or "").strip()
        if data.get("unit"):
            material.unit = data["unit"].strip()
        if "minimum_stock" in data and data["minimum_stock"] is not None:
            material.minimum_stock = data["minimum_stock"]
        if "description" in data:
            material.description = data["description"]
        if "legacy_code" in data:
            material.legacy_code = data["legacy_code"]
        if "is_active" in data and data["is_active"] is not None:
            material.is_active = data["is_active"]
        material.updated_by = self.user.id
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE,
            ResourceType.WAREHOUSE_MATERIAL,
            resource_id=material.id,
            resource_name=material.code,
            new_values=data,
        )
        return material

    async def get_material(self, material_id: int) -> WarehouseMaterial:
        material = await self.db.get(WarehouseMaterial, material_id)
        if material is None:
            raise ResourceNotFoundError(resource_type="物资", resource_id=material_id)
        return material

    async def _assert_unique_warehouse(
        self, code: str, name: str, exclude_id: int | None = None
    ) -> None:
        code_query = select(Warehouse).where(Warehouse.code == code.strip())
        name_query = select(Warehouse).where(Warehouse.name == name.strip())
        if exclude_id:
            code_query = code_query.where(Warehouse.id != exclude_id)
            name_query = name_query.where(Warehouse.id != exclude_id)
        if (await self.db.execute(code_query)).scalar_one_or_none():
            raise DuplicateRecordError(
                resource_type="库房", field_name="编码", field_value=code
            )
        if (await self.db.execute(name_query)).scalar_one_or_none():
            raise DuplicateRecordError(
                resource_type="库房", field_name="名称", field_value=name
            )

    async def _assert_warehouse_unused(self, warehouse_id: int) -> None:
        await self._assert_no_related_rows(
            warehouse_id,
            column_sets=(
                (
                    WarehouseDocumentLine.source_warehouse_id,
                    WarehouseDocumentLine.target_warehouse_id,
                ),
                (WarehouseStockBalance.warehouse_id,),
                (WarehouseCount.warehouse_id,),
                (WarehouseCountLine.warehouse_id,),
            ),
            message="库房已发生库存业务，不能删除。可先停用，或冲销相关单据后再删",
        )

    async def _assert_location_unused(self, location_id: int) -> None:
        await self._assert_no_related_rows(
            location_id,
            column_sets=(
                (
                    WarehouseDocumentLine.source_location_id,
                    WarehouseDocumentLine.target_location_id,
                ),
                (WarehouseStockBalance.location_id,),
                (WarehouseCount.location_id,),
                (WarehouseCountLine.location_id,),
            ),
            message="货位已发生库存业务，不能删除。可先停用，或冲销相关单据后再删",
        )

    async def _assert_no_related_rows(
        self, value: int, *, column_sets, message: str
    ) -> None:
        for columns in column_sets:
            condition = columns[0] == value
            for column in columns[1:]:
                condition = or_(condition, column == value)
            result = await self.db.execute(select(columns[0]).where(condition).limit(1))
            if result.scalar_one_or_none() is not None:
                raise ValidationError(message=message)

    async def _clear_default_location(self, warehouse_id: int) -> None:
        result = await self.db.execute(
            select(WarehouseLocation).where(
                WarehouseLocation.warehouse_id == warehouse_id
            )
        )
        for location in result.scalars().all():
            location.is_default = False
