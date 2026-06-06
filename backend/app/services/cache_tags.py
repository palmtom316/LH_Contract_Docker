"""
Cache Tag System for Efficient Cache Invalidation
Allows batch invalidation of related cache entries
"""
from enum import Enum
from typing import List
from app.core.cache import cache_manager


class CacheTag(str, Enum):
    """Cache tags for grouping related cache entries"""
    UPSTREAM_CONTRACT = "upstream_contract"
    DOWNSTREAM_CONTRACT = "downstream_contract"
    MANAGEMENT_CONTRACT = "management_contract"
    DASHBOARD = "dashboard"
    REPORTS = "reports"
    EXPENSES = "expenses"
    USERS = "users"
    AUDIT = "audit"


async def invalidate_by_tags(tags: List[CacheTag]) -> int:
    """Invalidate all cache entries matching the given tags"""
    total_cleared = 0
    for tag in tags:
        count = await cache_manager.clear_pattern(f"{tag.value}:*")
        total_cleared += count
    return total_cleared


async def invalidate_contract_caches(contract_type: str = "all") -> int:
    """Invalidate contract-related caches"""
    tags = [CacheTag.DASHBOARD, CacheTag.REPORTS]

    if contract_type == "upstream" or contract_type == "all":
        tags.append(CacheTag.UPSTREAM_CONTRACT)
    if contract_type == "downstream" or contract_type == "all":
        tags.append(CacheTag.DOWNSTREAM_CONTRACT)
    if contract_type == "management" or contract_type == "all":
        tags.append(CacheTag.MANAGEMENT_CONTRACT)

    return await invalidate_by_tags(tags)
