"""
Feature detection orchestration service.
Coordinates feature detector, cache, and image processing.

Features:
- Async feature detection
- Automatic caching
- Performance monitoring
- Error handling
- Request deduplication

Example Usage:
    service = FeatureService(feature_detector, cache, image_service, settings)
    result = await service.detect_features(upload_file, request_id)
"""

import time
from typing import Any

from fastapi import UploadFile

from services.feature_detector import FeatureDetector
from services.cache_service import RedisCacheService
from services.image_service import ImageService
from core.config import Settings
from core.logging_config import get_logger
from core.exceptions import ServiceNotReadyException

logger = get_logger(__name__)


class FeatureService:
    """
    Orchestrates feature detection with caching.
    
    Attributes:
        feature_detector: Feature detection model
        cache: Redis cache service
        image_service: Image validation service
        settings: Application settings
    
    Example:
        >>> service = FeatureService(detector, cache, img_service, settings)
        >>> result = await service.detect_features(file, "req-123")
        >>> print(result["keypoints"])  # 1247
    """
    
    def __init__(
        self,
        feature_detector: FeatureDetector,
        cache: RedisCacheService,
        image_service: ImageService,
        settings: Settings
    ):
        """
        Initialize feature service.
        
        Args:
            feature_detector: Feature detector instance
            cache: Cache service instance
            image_service: Image service instance
            settings: Application settings
        """
        self.feature_detector = feature_detector
        self.cache = cache
        self.image_service = image_service
        self.settings = settings
    
    async def detect_features(
        self,
        file: UploadFile,
        request_id: str
    ) -> dict[str, Any]:
        """
        Detect features in uploaded image with caching.
        
        Process:
        1. Validate and save image
        2. Generate cache key
        3. Check cache for existing result
        4. If miss, run feature detection
        5. Cache result
        6. Return result with metadata
        
        Args:
            file: Uploaded image file
            request_id: Unique request identifier
        
        Returns:
            Dictionary with detection results and metadata
        
        Raises:
            ServiceNotReadyException: If detector not ready
            ImageProcessingException: If image validation fails
        
        Example:
            >>> result = await service.detect_features(file, "abc-123")
            >>> print(result)
            {
                "keypoints": 1247,
                "descriptors_shape": (1247, 128),
                "cached": False,
                "processing_time_ms": 342.5
            }
        """
        start_time = time.perf_counter()
        file_path = None
        cached = False
        
        try:
            # Check if service is ready
            if not self.feature_detector.ready:
                logger.warning("Feature detector not ready", request_id=request_id)
                raise ServiceNotReadyException()
            
            # Step 1: Validate and save image
            logger.info("Validating image", request_id=request_id, filename=file.filename)
            file_path = await self.image_service.validate_and_save(file)
            
            # Step 2: Generate cache key
            cache_key = await self.image_service.generate_cache_key(file_path)
            
            # Step 3: Check cache
            if self.settings.cache_enabled:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    cached = True
                    processing_time = (time.perf_counter() - start_time) * 1000
                    
                    logger.info(
                        "Cache hit",
                        request_id=request_id,
                        cache_key=cache_key,
                        processing_time_ms=processing_time
                    )
                    
                    return {
                        **cached_result,
                        "cached": True,
                        "processing_time_ms": processing_time
                    }
            
            # Step 4: Process image (cache miss)
            logger.info("Processing image", request_id=request_id, file_path=file_path)
            detection_start = time.perf_counter()
            
            result = await self.feature_detector.process_image(file_path)
            
            detection_time = (time.perf_counter() - detection_start) * 1000
            
            # Step 5: Cache result
            cache_data = {
                "keypoints": result["keypoints"],
                "descriptors_shape": result["descriptors"]
            }
            
            if self.settings.cache_enabled:
                await self.cache.set(
                    cache_key,
                    cache_data,
                    ttl=self.settings.cache_ttl
                )
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                "Feature detection complete",
                request_id=request_id,
                keypoints=result["keypoints"],
                descriptors_shape=result["descriptors"],
                detection_time_ms=detection_time,
                total_time_ms=processing_time,
                cached=False
            )
            
            return {
                "keypoints": result["keypoints"],
                "descriptors_shape": result["descriptors"],
                "cached": False,
                "processing_time_ms": processing_time
            }
            
        finally:
            # Cleanup temporary file
            if file_path:
                await self.image_service.cleanup_file(file_path)

