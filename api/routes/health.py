"""
Health check endpoints.
Provides service health status and readiness checks.

Endpoints:
    - GET /health: Basic health check
    - GET /health/ready: Readiness probe (K8s compatible)
    - GET /health/live: Liveness probe (K8s compatible)
"""

import time

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

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
    description="Get service health status including detector and cache readiness"
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


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Check if service is ready to accept requests (K8s readiness probe)"
)
async def readiness_check(
    feature_detector: FeatureDetector = Depends(get_feature_detector),
    cache: RedisCacheService = Depends(get_cache_service)
) -> JSONResponse:
    """
    Kubernetes readiness probe.
    Returns 200 only if service can handle requests.
    
    Returns:
        200 OK if ready, 503 Service Unavailable if not
    """
    detector_ready = feature_detector.ready
    cache_connected = await cache.ping()
    
    if detector_ready and cache_connected:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "detector_ready": detector_ready,
                "cache_connected": cache_connected
            }
        )


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Check if service is alive (K8s liveness probe)"
)
async def liveness_check() -> JSONResponse:
    """
    Kubernetes liveness probe.
    Returns 200 if service is running (even if not fully ready).
    
    Returns:
        200 OK if alive
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive"}
    )

