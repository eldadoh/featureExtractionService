"""
FastAPI dependency injection.
Provides shared instances and lifecycle management.

Dependencies:
    - Settings: Application configuration
    - FeatureDetector: Feature detection model (singleton)
    - CacheService: Redis cache client
    - Services: Business logic services
"""

import uuid

from fastapi import Depends, Request

from services.feature_detector import FeatureDetector
from services.cache_service import RedisCacheService
from services.image_service import ImageService
from services.feature_service import FeatureService
from core.config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton instances
_feature_detector: FeatureDetector | None = None
_cache_service: RedisCacheService | None = None


def get_settings():
    """Get application settings."""
    return settings


async def get_feature_detector() -> FeatureDetector:
    """
    Get singleton feature detector instance.
    Ensures only one detector per worker.
    """
    global _feature_detector
    
    if _feature_detector is None:
        logger.info("Initializing FeatureDetector")
        _feature_detector = FeatureDetector()
        
        if not _feature_detector.ready:
            logger.info("Warming up FeatureDetector")
            await _feature_detector.warmup()
            logger.info("FeatureDetector ready")
    
    return _feature_detector


async def get_cache_service() -> RedisCacheService:
    """
    Get singleton cache service instance.
    Manages connection pool per worker.
    """
    global _cache_service
    
    if _cache_service is None:
        logger.info("Initializing RedisCacheService")
        _cache_service = RedisCacheService(settings)
        await _cache_service.connect()
        logger.info("RedisCacheService connected")
    
    return _cache_service


def get_image_service(
    settings=Depends(get_settings)
) -> ImageService:
    """
    Get image service instance.
    Stateless, can create per request.
    """
    return ImageService(settings)


async def get_feature_service(
    feature_detector: FeatureDetector = Depends(get_feature_detector),
    cache: RedisCacheService = Depends(get_cache_service),
    image_service: ImageService = Depends(get_image_service),
    settings=Depends(get_settings)
) -> FeatureService:
    """
    Get feature service with all dependencies injected.
    """
    return FeatureService(feature_detector, cache, image_service, settings)


def get_request_id(request: Request) -> str:
    """
    Get or generate request ID for tracing.
    
    Priority:
    1. X-Request-ID header
    2. Generate new UUID
    """
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id

