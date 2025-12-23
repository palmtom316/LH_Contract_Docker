"""
Cache Service Tests
Tests for the Redis caching functionality
"""
import pytest
from unittest.mock import AsyncMock, patch
import json

from app.core.cache import CacheManager, cache_manager


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager for testing"""
    manager = CacheManager()
    manager.use_redis = False  # Use in-memory cache
    manager.memory_cache = {}
    return manager


@pytest.mark.asyncio
class TestCacheManager:
    """Test CacheManager methods"""
    
    async def test_set_and_get(self, mock_cache_manager: CacheManager):
        """Test setting and getting cache values"""
        await mock_cache_manager.set("test_key", {"data": "value"}, ttl=300)
        
        result = await mock_cache_manager.get("test_key")
        
        assert result is not None
        assert result["data"] == "value"
    
    async def test_get_nonexistent_key(self, mock_cache_manager: CacheManager):
        """Test getting a non-existent key"""
        result = await mock_cache_manager.get("nonexistent_key")
        
        assert result is None
    
    async def test_delete_key(self, mock_cache_manager: CacheManager):
        """Test deleting a cache key"""
        # Set a value
        await mock_cache_manager.set("delete_test", {"data": "value"})
        
        # Verify it exists
        assert await mock_cache_manager.get("delete_test") is not None
        
        # Delete it
        await mock_cache_manager.delete("delete_test")
        
        # Verify it's gone
        assert await mock_cache_manager.get("delete_test") is None
    
    async def test_clear_pattern(self, mock_cache_manager: CacheManager):
        """Test clearing keys by pattern"""
        # Set multiple keys
        await mock_cache_manager.set("report:2024:1", {"data": 1})
        await mock_cache_manager.set("report:2024:2", {"data": 2})
        await mock_cache_manager.set("other:key", {"data": 3})
        
        # Clear only report keys
        count = await mock_cache_manager.clear_pattern("report:*")
        
        assert count == 2
        assert await mock_cache_manager.get("report:2024:1") is None
        assert await mock_cache_manager.get("report:2024:2") is None
        assert await mock_cache_manager.get("other:key") is not None
    
    async def test_make_key(self, mock_cache_manager: CacheManager):
        """Test cache key generation"""
        key1 = mock_cache_manager._make_key("prefix", 1, 2, name="test")
        key2 = mock_cache_manager._make_key("prefix", 1, 2, name="test")
        key3 = mock_cache_manager._make_key("prefix", 1, 3, name="test")
        
        # Same arguments should produce same key
        assert key1 == key2
        
        # Different arguments should produce different key
        assert key1 != key3
    
    async def test_cached_decorator(self, mock_cache_manager: CacheManager):
        """Test the cached decorator"""
        call_count = 0
        
        @mock_cache_manager.cached(ttl=300, key_prefix="test_func")
        async def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - should execute function
        result1 = await expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call with same args - should return cached value
        result2 = await expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not have increased
        
        # Call with different args - should execute function again
        result3 = await expensive_function(3, 4)
        assert result3 == 7
        assert call_count == 2


@pytest.mark.asyncio
class TestReportCacheService:
    """Test report caching service"""
    
    async def test_cache_report_data(self, mock_cache_manager: CacheManager):
        """Test caching report data"""
        report_data = {
            "year": 2024,
            "total": 100000,
            "items": [{"name": "A", "value": 50000}]
        }
        
        # Cache the data
        await mock_cache_manager.set("reports:finance:2024", report_data)
        
        # Retrieve the data
        cached = await mock_cache_manager.get("reports:finance:2024")
        
        assert cached is not None
        assert cached["year"] == 2024
        assert cached["total"] == 100000
        assert len(cached["items"]) == 1
    
    async def test_cache_serialization(self, mock_cache_manager: CacheManager):
        """Test that complex data types are properly serialized"""
        from datetime import date
        from decimal import Decimal
        
        # Note: dates and Decimals need to be serialized to strings
        data = {
            "date": str(date.today()),
            "amount": str(Decimal("12345.67")),
            "nested": {
                "list": [1, 2, 3],
                "dict": {"key": "value"}
            }
        }
        
        await mock_cache_manager.set("complex_data", data)
        
        cached = await mock_cache_manager.get("complex_data")
        
        assert cached is not None
        assert cached["date"] == str(date.today())
        assert cached["amount"] == "12345.67"
        assert cached["nested"]["list"] == [1, 2, 3]


@pytest.mark.asyncio
class TestCacheInvalidation:
    """Test cache invalidation scenarios"""
    
    async def test_invalidate_on_data_change(self, mock_cache_manager: CacheManager):
        """Test invalidating cache when data changes"""
        # Simulate cached report
        await mock_cache_manager.set("reports:contracts:2024", {"count": 10})
        
        # Verify it's cached
        assert await mock_cache_manager.get("reports:contracts:2024") is not None
        
        # Simulate data change - invalidate cache
        await mock_cache_manager.delete("reports:contracts:2024")
        
        # Verify cache is cleared
        assert await mock_cache_manager.get("reports:contracts:2024") is None
    
    async def test_invalidate_by_year(self, mock_cache_manager: CacheManager):
        """Test invalidating all caches for a specific year"""
        # Set caches for different years
        await mock_cache_manager.set("reports:finance:2023", {"year": 2023})
        await mock_cache_manager.set("reports:finance:2024", {"year": 2024})
        await mock_cache_manager.set("reports:contracts:2024", {"year": 2024})
        
        # Clear only 2024 reports
        count = await mock_cache_manager.clear_pattern("reports:*:2024*")
        
        # 2023 should still exist
        assert await mock_cache_manager.get("reports:finance:2023") is not None
