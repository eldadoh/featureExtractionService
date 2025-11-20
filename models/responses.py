"""
Pydantic models for API responses.
Ensures consistent response structure.

Models:
    - FeatureDetectionResponse: Successful feature detection result
    - ErrorResponse: Error response format
    - HealthResponse: Health check response
"""

from typing import Any
from pydantic import BaseModel, Field


class FeatureDetectionResponse(BaseModel):
    """
    Response model for successful feature detection.
    
    Attributes:
        success: Whether operation succeeded
        keypoints: Number of detected keypoints
        descriptors_shape: Shape of descriptor array (rows, cols)
        cached: Whether result was served from cache
        processing_time_ms: Processing time in milliseconds
        request_id: Unique request identifier
    
    Example Output:
        {
            "success": true,
            "keypoints": 1247,
            "descriptors_shape": [1247, 128],
            "cached": false,
            "processing_time_ms": 342.5,
            "request_id": "abc123-def456"
        }
    """
    
    success: bool = Field(default=True, description="Operation success status")
    keypoints: int = Field(ge=0, description="Number of detected keypoints")
    descriptors_shape: tuple[int, int] = Field(description="Shape of descriptors array")
    cached: bool = Field(description="Whether result was from cache")
    processing_time_ms: float = Field(ge=0, description="Processing time in milliseconds")
    request_id: str = Field(description="Unique request identifier")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "keypoints": 1247,
                    "descriptors_shape": [1247, 128],
                    "cached": False,
                    "processing_time_ms": 342.5,
                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    Attributes:
        success: Always False for errors
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional error context
        request_id: Unique request identifier
    
    Example Output:
        {
            "success": false,
            "error_code": "IMAGE_TOO_LARGE",
            "message": "Image size 15.2MB exceeds limit of 10MB",
            "details": {"size_mb": 15.2, "max_size_mb": 10},
            "request_id": "abc123-def456"
        }
    """
    
    success: bool = Field(default=False, description="Always False for errors")
    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    request_id: str | None = Field(default=None, description="Request identifier if available")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error_code": "INVALID_IMAGE",
                    "message": "Invalid image format or corrupted file",
                    "details": {"extension": "txt"},
                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """
    Health check response.
    
    Attributes:
        status: Health status (healthy/unhealthy)
        service: Service name
        version: API version
        feature_detector_ready: Whether feature detector is warmed up
        cache_connected: Whether Redis is connected
        uptime_seconds: Service uptime
    
    Example Output:
        {
            "status": "healthy",
            "service": "Feature Detection API",
            "version": "1.0.0",
            "feature_detector_ready": true,
            "cache_connected": true,
            "uptime_seconds": 1234.5
        }
    """
    
    status: str = Field(description="Health status")
    service: str = Field(description="Service name")
    version: str = Field(description="API version")
    feature_detector_ready: bool = Field(description="Feature detector warmup status")
    cache_connected: bool = Field(description="Redis connection status")
    uptime_seconds: float = Field(ge=0, description="Service uptime in seconds")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "service": "Feature Detection API",
                    "version": "1.0.0",
                    "feature_detector_ready": True,
                    "cache_connected": True,
                    "uptime_seconds": 1234.5
                }
            ]
        }
    }

