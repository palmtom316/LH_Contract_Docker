"""Warehouse inventory period open / close / reopen."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppException, ErrorCode, ValidationError
from app.core.permissions import Permission, has_permission
from app.core.timezone import business_today, period_key
from app.models.user import User
from app.models.warehouse import PeriodStatus, WarehousePeriod
from app.services.audit_service import AuditAction, ResourceType, create_audit_log


class WarehousePeriodService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    def can_manage(self) -> bool:
        return bool(
            self.user.is_superuser
            or has_permission(self.user, Permission.MANAGE_WAREHOUSE_PERIODS)
        )

    async def list_periods(self) -> list[WarehousePeriod]:
        result = await self.db.execute(
            select(WarehousePeriod).order_by(
                WarehousePeriod.year.desc(), WarehousePeriod.month.desc()
            )
        )
        return list(result.scalars().all())

    async def ensure_current_open(self) -> WarehousePeriod:
        today = business_today()
        return await self._get_or_create(today.year, today.month, open_if_missing=True)

    async def get_period(self, year: int, month: int) -> WarehousePeriod | None:
        result = await self.db.execute(
            select(WarehousePeriod).where(
                WarehousePeriod.year == year, WarehousePeriod.month == month
            )
        )
        return result.scalar_one_or_none()

    async def close_period(self, year: int, month: int) -> WarehousePeriod:
        if not self.can_manage():
            raise AppException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message="只有库房管理员可以结账",
                status_code=403,
            )
        self._validate_month(year, month)
        period = await self._get_or_create(year, month, open_if_missing=True, for_update=True)
        if period.status == PeriodStatus.CLOSED.value:
            raise ValidationError(message="该期间已经结账")
        now = datetime.now(timezone.utc)
        period.status = PeriodStatus.CLOSED.value
        period.closed_by = self.user.id
        period.closed_at = now
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE,
            ResourceType.WAREHOUSE_PERIOD,
            resource_id=period.id,
            resource_name=f"{year:04d}-{month:02d}",
            description=f"结账库存期间 {year:04d}-{month:02d}",
            old_values={"status": PeriodStatus.OPEN.value},
            new_values={"status": PeriodStatus.CLOSED.value},
        )
        return period

    async def reopen_period(self, year: int, month: int, reason: str) -> WarehousePeriod:
        if not self.can_manage():
            raise AppException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message="只有库房管理员可以反结账",
                status_code=403,
            )
        if not (reason or "").strip():
            raise ValidationError(message="反结账必须填写原因")
        self._validate_month(year, month)
        period = await self._get_or_create(year, month, open_if_missing=False, for_update=True)
        if period is None:
            raise ValidationError(message="期间不存在，无需反结账")
        if period.status != PeriodStatus.CLOSED.value:
            raise ValidationError(message="仅已结账期间可以反结账")
        now = datetime.now(timezone.utc)
        period.status = PeriodStatus.OPEN.value
        period.reopened_by = self.user.id
        period.reopened_at = now
        period.reopen_reason = reason.strip()
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.APPROVE,
            ResourceType.WAREHOUSE_PERIOD,
            resource_id=period.id,
            resource_name=f"{year:04d}-{month:02d}",
            description=f"反结账库存期间 {year:04d}-{month:02d}: {reason.strip()}",
            old_values={"status": PeriodStatus.CLOSED.value},
            new_values={
                "status": PeriodStatus.OPEN.value,
                "reopen_reason": reason.strip(),
            },
        )
        return period

    async def assert_posting_allowed(self, occurred_on: date) -> WarehousePeriod:
        year, month = period_key(occurred_on)
        self._validate_month(year, month)
        today = business_today()
        current_year, current_month = period_key(today)
        await self.ensure_current_open()
        is_current = (year, month) == (current_year, current_month)
        period = await self._get_or_create(
            year,
            month,
            open_if_missing=self.can_manage() or is_current,
            for_update=True,
        )
        if period is None:
            raise AppException(
                error_code=ErrorCode.PERIOD_CLOSED,
                message="历史期间尚未开放，不能过账",
                detail="普通库管只能在已开放期间过账，历史补录请库房管理员先开放期间",
                status_code=409,
            )
        if period.status == PeriodStatus.CLOSED.value:
            raise AppException(
                error_code=ErrorCode.PERIOD_CLOSED,
                message="该库存期间已结账，禁止过账",
                detail="如需历史补录，请库房管理员反结账并记录原因",
                status_code=409,
            )
        return period

    async def assert_document_period_editable(self, occurred_on: date) -> None:
        year, month = period_key(occurred_on)
        period = await self.get_period(year, month)
        if period is not None and period.status == PeriodStatus.CLOSED.value:
            raise AppException(
                error_code=ErrorCode.PERIOD_CLOSED,
                message="已结账单据禁止补录修改",
                status_code=409,
            )

    async def _get_or_create(
        self,
        year: int,
        month: int,
        *,
        open_if_missing: bool,
        for_update: bool = False,
    ) -> WarehousePeriod | None:
        query = select(WarehousePeriod).where(
            WarehousePeriod.year == year, WarehousePeriod.month == month
        )
        if for_update:
            query = query.with_for_update()
        result = await self.db.execute(query)
        period = result.scalar_one_or_none()
        if period is not None:
            return period
        if not open_if_missing:
            return None
        await self.db.execute(
            insert(WarehousePeriod)
            .values(year=year, month=month, status=PeriodStatus.OPEN.value)
            .on_conflict_do_nothing(index_elements=["year", "month"])
        )
        await self.db.flush()
        query = select(WarehousePeriod).where(
            WarehousePeriod.year == year, WarehousePeriod.month == month
        )
        if for_update:
            query = query.with_for_update()
        result = await self.db.execute(query)
        return result.scalar_one()

    @staticmethod
    def _validate_month(year: int, month: int) -> None:
        if year < 2000 or year > 2100 or month < 1 or month > 12:
            raise ValidationError(message="库存期间无效")
