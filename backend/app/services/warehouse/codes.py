"""Warehouse material and document number generators."""

from __future__ import annotations

import hashlib
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import (
    DOCUMENT_NO_PREFIX,
    SUPPLY_CONDITION_SEGMENT,
    DocumentType,
    MaterialCategory,
    MaterialCondition,
    SupplyType,
    WarehouseCodeCounter,
    WarehouseDocumentCounter,
)

_SPACE_RE = re.compile(r"\s+")


def normalize_identity_part(value: str | None) -> str:
    return _SPACE_RE.sub(" ", (value or "").strip()).casefold()


def material_identity_key(
    name: str,
    brand: str,
    specification: str,
    unit: str,
    condition: str | MaterialCondition,
    supply_type: str | SupplyType,
) -> str:
    payload = "|".join(
        [
            normalize_identity_part(name),
            normalize_identity_part(brand),
            normalize_identity_part(specification),
            normalize_identity_part(unit),
            normalize_identity_part(
                condition.value if isinstance(condition, MaterialCondition) else condition
            ),
            normalize_identity_part(
                supply_type.value if isinstance(supply_type, SupplyType) else supply_type
            ),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def supply_condition_segment(
    supply_type: str | SupplyType,
    condition: str | MaterialCondition,
) -> str:
    supply = SupplyType(supply_type)
    cond = MaterialCondition(condition)
    try:
        return SUPPLY_CONDITION_SEGMENT[(supply, cond)]
    except KeyError as exc:
        raise ValueError(f"不支持的供应/成色组合: {supply.value}/{cond.value}") from exc


def format_sequence(number: int, min_width: int) -> str:
    width = min_width if number < 10**min_width else len(str(number))
    return f"{number:0{width}d}"


async def generate_material_code(
    db: AsyncSession,
    category: str | MaterialCategory,
    supply_type: str | SupplyType,
    condition: str | MaterialCondition,
) -> str:
    cat = MaterialCategory(category)
    segment = supply_condition_segment(supply_type, condition)

    insert_stmt = (
        insert(WarehouseCodeCounter)
        .values(category=cat.value, supply_condition=segment, next_number=1)
        .on_conflict_do_nothing(index_elements=["category", "supply_condition"])
    )
    await db.execute(insert_stmt)
    await db.flush()

    result = await db.execute(
        select(WarehouseCodeCounter)
        .where(
            WarehouseCodeCounter.category == cat.value,
            WarehouseCodeCounter.supply_condition == segment,
        )
        .with_for_update()
    )
    counter = result.scalar_one()
    number = int(counter.next_number)
    counter.next_number = number + 1
    await db.flush()
    return f"{cat.value}-{segment}-{format_sequence(number, 3)}"


async def generate_document_no(
    db: AsyncSession,
    document_type: str | DocumentType,
    occurred_on: date,
) -> str:
    doc_type = DocumentType(document_type)
    prefix = DOCUMENT_NO_PREFIX[doc_type]

    insert_stmt = (
        insert(WarehouseDocumentCounter)
        .values(prefix=prefix, occurred_on=occurred_on, next_number=1)
        .on_conflict_do_nothing(index_elements=["prefix", "occurred_on"])
    )
    await db.execute(insert_stmt)
    await db.flush()

    result = await db.execute(
        select(WarehouseDocumentCounter)
        .where(
            WarehouseDocumentCounter.prefix == prefix,
            WarehouseDocumentCounter.occurred_on == occurred_on,
        )
        .with_for_update()
    )
    counter = result.scalar_one()
    number = int(counter.next_number)
    counter.next_number = number + 1
    await db.flush()
    return f"{prefix}-{occurred_on.strftime('%Y%m%d')}-{format_sequence(number, 4)}"
