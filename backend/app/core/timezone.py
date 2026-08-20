"""Business timezone helpers.

Warehouse documents use a calendar date (`occurred_on` / `counted_on`), not an
instant. Default dates must follow Asia/Shanghai so China overnight work is not
shifted to the previous UTC day.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

BUSINESS_TZ = ZoneInfo("Asia/Shanghai")
BUSINESS_TZ_NAME = "Asia/Shanghai"


def business_now() -> datetime:
    return datetime.now(BUSINESS_TZ)


def business_today() -> date:
    return business_now().date()


def period_key(value: date) -> tuple[int, int]:
    return value.year, value.month
