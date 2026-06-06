"""
Dictionary usage scanning for safe upgrade operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationError
from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.models.contract_downstream import FinanceDownstreamPayable
from app.models.contract_management import FinanceManagementPayable
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceivable
from app.models.expense import ExpenseNonContract
from app.models.system import SysDictionary


@dataclass(frozen=True)
class DictionaryReferenceTarget:
    model: object
    column_name: str
    label: str


REFERENCE_MAP: Dict[str, List[DictionaryReferenceTarget]] = {
    "expense_type": [
        DictionaryReferenceTarget(
            model=ExpenseNonContract,
            column_name="expense_type",
            label="expenses_non_contract.expense_type",
        )
    ],
    "payment_category": [
        DictionaryReferenceTarget(
            model=FinanceUpstreamReceivable,
            column_name="category",
            label="finance_upstream_receivables.category",
        ),
        DictionaryReferenceTarget(
            model=FinanceDownstreamPayable,
            column_name="category",
            label="finance_downstream_payables.category",
        ),
        DictionaryReferenceTarget(
            model=FinanceManagementPayable,
            column_name="category",
            label="finance_management_payables.category",
        ),
    ],
    "contract_category": [
        DictionaryReferenceTarget(
            model=ContractUpstream,
            column_name="category",
            label="contracts_upstream.category",
        )
    ],
    "project_category": [
        DictionaryReferenceTarget(
            model=ContractUpstream,
            column_name="company_category",
            label="contracts_upstream.company_category",
        )
    ],
    "downstream_contract_category": [
        DictionaryReferenceTarget(
            model=ContractDownstream,
            column_name="category",
            label="contracts_downstream.category",
        )
    ],
    "management_contract_category": [
        DictionaryReferenceTarget(
            model=ContractManagement,
            column_name="category",
            label="contracts_management.category",
        )
    ],
}


class DictionaryUsageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage_summary(self, category: str, value: str) -> Dict[str, object]:
        targets = REFERENCE_MAP.get(category, [])
        references: List[Dict[str, object]] = []
        total = 0

        for target in targets:
            column = getattr(target.model, target.column_name)
            count = (
                await self.db.execute(
                    select(func.count()).select_from(target.model).where(column == value)
                )
            ).scalar_one()
            if count:
                references.append({"field": target.label, "count": count})
                total += count

        return {
            "category": category,
            "value": value,
            "total_references": total,
            "references": references,
        }

    async def ensure_value_change_is_safe(
        self,
        dictionary: SysDictionary,
        new_value: str,
    ) -> None:
        if dictionary.value == new_value:
            return

        usage = await self.get_usage_summary(dictionary.category, dictionary.value)
        if usage["total_references"] > 0:
            raise ValidationError(
                message="字典值已被历史数据引用，禁止直接修改存储值",
                field_errors={
                    "value": "请新增替代字典值并停用旧值，不要覆盖历史记录使用中的 value"
                },
            )

    async def disable_or_delete(
        self,
        dictionary: SysDictionary,
        replacement_value: str | None = None,
    ) -> Dict[str, object]:
        usage = await self.get_usage_summary(dictionary.category, dictionary.value)

        if usage["total_references"] == 0:
            await self.db.delete(dictionary)
            await self.db.commit()
            return {"message": "Option deleted", "deletion_mode": "deleted", "usage": usage}

        if replacement_value:
            replacement = (
                await self.db.execute(
                    select(SysDictionary).where(
                        SysDictionary.category == dictionary.category,
                        SysDictionary.value == replacement_value,
                    )
                )
            ).scalar_one_or_none()
            if not replacement:
                raise ValidationError(
                    message="替代字典值不存在",
                    field_errors={"replacement_value": "请先创建 replacement_value 对应的字典项"},
                )

        dictionary.is_active = False
        await self.db.commit()
        await self.db.refresh(dictionary)
        return {
            "message": "字典值已被历史数据引用，已停用以保护历史记录",
            "deletion_mode": "disabled",
            "usage": usage,
            "replacement_value": replacement_value,
        }
