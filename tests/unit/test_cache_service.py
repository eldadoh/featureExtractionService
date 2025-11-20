"""
Unit tests for Redis cache service.
Tests caching operations, error handling, and connection management.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from redis.exceptions import RedisError

from services.cache_service import RedisCacheService
from core.config import Settings


class TestRedisCacheService:
    """Test suite for RedisCacheService."""
    
    @pytest_asyncio.fixture
    async def cache_service(self, test_settings: Settings) -> RedisCacheService:
        """Create cache service instance."""
        return RedisCacheService(test_settings)
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service: RedisCacheService):
        """Test setting and getting cache values."""
        with patch.object(cache_service, 'client') as mock_client:
            cache_service._connected = True
            mock_client.get = AsyncMock(return_value='{"key": "value"}')
            mock_client.set = AsyncMock(return_value=True)
            
            # Set value
            result = await cache_service.set("test_key", {"key": "value"})
            assert result is True
            
            # Get value
            value = await cache_service.get("test_key")
            assert value == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service: RedisCacheService):
        """Test cache miss returns None."""
        with patch.object(cache_service, 'client') as mock_client:
            cache_service._connected = True
            mock_client.get = AsyncMock(return_value=None)
            
            value = await cache_service.get("nonexistent_key")
            assert value is None
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_error(self, cache_service: RedisCacheService):
        """Test graceful degradation when cache operations fail."""
        with patch.object(cache_service, 'client') as mock_client:
            cache_service._connected = True
            mock_client.get = AsyncMock(side_effect=RedisError("Redis connection error"))
            
            # Should return None instead of raising
            value = await cache_service.get("test_key")
            assert value is None

