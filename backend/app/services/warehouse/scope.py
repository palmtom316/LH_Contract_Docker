"""Warehouse authorization scope checks."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException, ErrorCode, PermissionDeniedError
from app.core.permissions import Permission, has_permission
from app.models.user import User, UserRole
from app.models.warehouse import Warehouse, WarehouseUserScope


class WarehouseScopeService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    def can_view_all(self) -> bool:
        return bool(
            self.user.is_superuser
            or self.user.role in {UserRole.ADMIN, UserRole.WAREHOUSE_ADMIN, UserRole.COMPANY_LEADER}
            or has_permission(self.user, Permission.VIEW_ALL_WAREHOUSES)
        )

    def can_post_all(self) -> bool:
        return bool(
            self.user.is_superuser
            or self.user.role in {UserRole.ADMIN, UserRole.WAREHOUSE_ADMIN}
        )

    async def authorized_warehouse_ids(self, *, for_posting: bool = False) -> Optional[set[int]]:
        if for_posting and self.can_post_all():
            return None
        if not for_posting and self.can_view_all():
            return None

        result = await self.db.execute(
            select(WarehouseUserScope)
            .options(selectinload(WarehouseUserScope.warehouse))
            .where(WarehouseUserScope.user_id == self.user.id)
        )
        scopes = result.scalars().all()
        allowed: set[int] = set()
        for scope in scopes:
            warehouse = scope.warehouse
            if warehouse is None or not warehouse.is_active:
                continue
            if not self.user.is_active:
                continue
            allowed.add(scope.warehouse_id)
        return allowed

    async def default_warehouse_id(self) -> Optional[int]:
        result = await self.db.execute(
            select(WarehouseUserScope.warehouse_id).where(
                WarehouseUserScope.user_id == self.user.id,
                WarehouseUserScope.is_default.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_scopes(self, user_id: int) -> Sequence[WarehouseUserScope]:
        result = await self.db.execute(
            select(WarehouseUserScope)
            .options(selectinload(WarehouseUserScope.warehouse))
            .where(WarehouseUserScope.user_id == user_id)
            .order_by(WarehouseUserScope.id)
        )
        return result.scalars().all()

    async def assert_warehouse_access(
        self,
        warehouse_id: int,
        *,
        for_posting: bool = False,
        action: str = "访问",
    ) -> Warehouse:
        warehouse = await self.db.get(Warehouse, warehouse_id)
        if warehouse is None:
            raise AppException(
                error_code=ErrorCode.WAREHOUSE_NOT_FOUND,
                message="库房不存在",
                detail=f"未找到库房 ID {warehouse_id}",
                status_code=404,
            )
        if not warehouse.is_active and for_posting:
            raise AppException(
                error_code=ErrorCode.WAREHOUSE_SCOPE_DENIED,
                message="库房已停用，不能过账",
                status_code=403,
            )
        allowed = await self.authorized_warehouse_ids(for_posting=for_posting)
        if allowed is not None and warehouse_id not in allowed:
            raise AppException(
                error_code=ErrorCode.WAREHOUSE_SCOPE_DENIED,
                message=f"无权{action}该库房",
                detail=f"库房 {warehouse.code} 不在授权范围",
                status_code=403,
            )
        return warehouse

    async def assert_warehouses_access(
        self,
        warehouse_ids: Iterable[int],
        *,
        for_posting: bool = False,
        action: str = "访问",
    ) -> None:
        seen: set[int] = set()
        for warehouse_id in warehouse_ids:
            if warehouse_id in seen:
                continue
            seen.add(warehouse_id)
            await self.assert_warehouse_access(
                warehouse_id, for_posting=for_posting, action=action
            )

    async def replace_scopes(self, user_id: int, items: list[dict]) -> Sequence[WarehouseUserScope]:
        if not has_permission(self.user, Permission.MANAGE_WAREHOUSE_MASTER) and not (
            self.user.is_superuser or self.user.role == UserRole.ADMIN
        ):
            raise PermissionDeniedError(detail="只有库房管理员可以维护库房授权")

        result = await self.db.execute(
            select(WarehouseUserScope).where(WarehouseUserScope.user_id == user_id)
        )
        for existing in result.scalars().all():
            await self.db.delete(existing)
        await self.db.flush()

        default_seen = False
        created: list[WarehouseUserScope] = []
        for item in items:
            warehouse = await self.db.get(Warehouse, item["warehouse_id"])
            if warehouse is None:
                raise AppException(
                    error_code=ErrorCode.WAREHOUSE_NOT_FOUND,
                    message="库房不存在",
                    status_code=404,
                )
            is_default = bool(item.get("is_default")) and not default_seen
            if is_default:
                default_seen = True
            scope = WarehouseUserScope(
                user_id=user_id,
                warehouse_id=warehouse.id,
                is_default=is_default,
            )
            self.db.add(scope)
            created.append(scope)
        await self.db.flush()
        return await self.list_scopes(user_id)
