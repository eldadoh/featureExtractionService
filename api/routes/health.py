"""
Health check endpoints.

Endpoints:
    - GET /health: Basic health check
"""

import time

from fastapi import APIRouter, Depends

from api.dependencies import (
    get_feature_detector,
    get_cache_service,
    get_settings
)
from services.feature_detector import FeatureDetector
from services.cache_service import RedisCacheService
from core.config import Settings
from models.responses import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

# Track service start time
_start_time = time.time()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Get service health status"
)
async def health_check(
    feature_detector: FeatureDetector = Depends(get_feature_detector),
    cache: RedisCacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """
    Comprehensive health check.
    
    Returns:
        Health status with all component statuses
    
    Example Response:
        {
            "status": "healthy",
            "service": "Feature Detection API",
            "version": "1.0.0",
            "feature_detector_ready": true,
            "cache_connected": true,
            "uptime_seconds": 1234.5
        }
    """
    detector_ready = feature_detector.ready
    cache_connected = await cache.ping()
    
    uptime = time.time() - _start_time
    
    # Overall health: healthy if both components are ready
    overall_status = "healthy" if (detector_ready and cache_connected) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        feature_detector_ready=detector_ready,
        cache_connected=cache_connected,
        uptime_seconds=uptime
    )
