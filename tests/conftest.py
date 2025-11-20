"""
Pytest configuration and shared fixtures.
Provides test utilities and mock objects.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from io import BytesIO

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import services and models (lightweight)
from services.feature_detector import FeatureDetector
from services.cache_service import RedisCacheService
from services.image_service import ImageService
from core.config import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        redis_host="localhost",
        redis_port=6379,
        cache_enabled=True,
        cache_ttl=60,
        max_image_size_mb=10,
        log_level="DEBUG",
        environment="development"
    )


@pytest.fixture
def mock_feature_detector() -> MagicMock:
    """Create mock feature detector."""
    detector = MagicMock(spec=FeatureDetector)
    detector.ready = True
    detector.warmup = AsyncMock()
    detector.process_image = AsyncMock(return_value={
        "keypoints": 100,
        "descriptors": (100, 128)
    })
    return detector


@pytest_asyncio.fixture
async def mock_cache_service(test_settings: Settings) -> AsyncMock:
    """Create mock cache service."""
    cache = AsyncMock(spec=RedisCacheService)
    cache.connect = AsyncMock()
    cache.disconnect = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.ping = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_image_service(test_settings: Settings) -> MagicMock:
    """Create mock image service."""
    service = MagicMock(spec=ImageService)
    service.validate_and_save = AsyncMock(return_value="/tmp/test.jpg")
    service.generate_cache_key = AsyncMock(return_value="features:abc123")
    service.cleanup_file = AsyncMock()
    return service


@pytest.fixture
def test_client() -> TestClient:
    """Create test client."""
    # Import app only when fixture is used (lazy loading)
    from api.main import app
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    # Import app only when fixture is used (lazy loading)
    from api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_image_path() -> str:
    """Path to sample test image."""
    return "data/images/lena_color_256.tif"


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Sample image content."""
    # Create a minimal valid PNG
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

