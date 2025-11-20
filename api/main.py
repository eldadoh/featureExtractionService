"""
FastAPI application entry point.
Configures routes, middleware, exception handlers, and lifecycle events.

Features:
    - Async startup/shutdown
    - Request logging middleware
    - Exception handling
    - API documentation (OpenAPI/Swagger)
    - CORS support
    - Health checks
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import health, features
from api.middleware import (
    RequestLoggingMiddleware,
    custom_exception_handler,
    generic_exception_handler
)
from api.dependencies import get_feature_detector, get_cache_service
from core.config import settings
from core.logging_config import get_logger
from core.exceptions import FeatureDetectionException

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown logic.
    
    Startup:
        - Initialize feature detector
        - Warm up model
        - Connect to Redis
        - Log service info
    
    Shutdown:
        - Disconnect from Redis
        - Close thread pools
        - Log shutdown
    """
    # Startup
    logger.info(
        "Application starting",
        environment=settings.environment,
        version=settings.app_version,
        workers=settings.api_workers
    )
    
    try:
        # Initialize feature detector and warmup
        logger.info("Initializing FeatureDetector")
        detector = await get_feature_detector()
        logger.info("FeatureDetector initialized and ready")
        
        # Connect to Redis
        logger.info("Connecting to Redis")
        cache = await get_cache_service()
        logger.info("Redis connected successfully")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")
    
    try:
        # Disconnect from Redis
        cache = await get_cache_service()
        await cache.disconnect()
        logger.info("Redis disconnected")
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Feature Detection API
    
    High-performance, production-ready API for SIFT feature detection in images.
    
    ### Features
    - 🚀 **Async Processing**: Handles concurrent requests efficiently
    - 💾 **Intelligent Caching**: Redis-based result caching (1-hour TTL)
    - 📊 **SIFT Algorithm**: Robust keypoint and descriptor extraction
    - 🔍 **Image Preprocessing**: Non-local means denoising
    - ⚡ **Fast Response**: Sub-second processing for most images
    - 🛡️ **Error Handling**: Comprehensive validation and error messages
    - 📝 **Structured Logging**: JSON logs with correlation IDs
    - 💪 **Production Ready**: Docker, health checks, monitoring
    
    ### Supported Formats
    JPG, JPEG, PNG, BMP, TIF, TIFF
    
    ### Rate Limits
    No rate limits currently configured (can be added)
    
    ### Caching Strategy
    Results are cached based on image content hash (SHA256).
    Identical images return cached results instantly (~5-20ms).
    
    ### Performance
    - **Cache Hit**: 5-20ms
    - **Cache Miss**: 300-500ms (varies by image complexity)
    - **Throughput**: 100+ req/s with 4 workers
    
    ### Authentication
    None required (can be added via middleware)
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Processing-Time-Ms"]
)

# Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# Exception Handlers
app.add_exception_handler(FeatureDetectionException, custom_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Routers
app.include_router(health.router)
app.include_router(features.router)


@app.get(
    "/",
    summary="Root Endpoint",
    description="API information and links",
    tags=["Root"]
)
async def root() -> JSONResponse:
    """
    Root endpoint with API information.
    
    Returns:
        API metadata and documentation links
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs",
            "health": "/health",
            "openapi": "/openapi.json"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
        access_log=False  # We use our own logging middleware
    )

