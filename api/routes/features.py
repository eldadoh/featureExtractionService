"""
Feature detection API endpoints.
Handles image upload and feature extraction requests.

Endpoints:
    - POST /api/v1/features/detect: Detect features in uploaded image
"""

from fastapi import APIRouter, Depends, UploadFile, File, status

from api.dependencies import get_feature_service, get_request_id
from services.feature_service import FeatureService
from models.responses import FeatureDetectionResponse
from core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/features", tags=["Features"])


@router.post(
    "/detect",
    response_model=FeatureDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect Image Features",
    description="""
    Detect SIFT features in an uploaded image.
    
    **Process:**
    1. Upload image (max 10MB)
    2. Validate image format and size
    3. Check cache for existing result
    4. If cache miss, run SIFT feature detection
    5. Cache result for 1 hour
    6. Return keypoints count and descriptors
    
    **Supported Formats:** JPG, PNG, BMP, TIF/TIFF
    
    **Caching:** Results are cached based on image content (SHA256 hash).
    Same image will return cached result instantly.
    
    **Performance:**
    - Cache hit: ~5-20ms
    - Cache miss: ~300-500ms (depends on image size/complexity)
    """,
    responses={
        200: {
            "description": "Successful feature detection",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "keypoints": 1247,
                        "descriptors_shape": [1247, 128],
                        "cached": False,
                        "processing_time_ms": 342.5,
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        400: {
            "description": "Invalid image format",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "INVALID_IMAGE",
                        "message": "Invalid image format or corrupted file",
                        "details": {},
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        413: {
            "description": "Image too large",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "IMAGE_TOO_LARGE",
                        "message": "Image size 15.2MB exceeds limit of 10MB",
                        "details": {"size_mb": 15.2, "max_size_mb": 10},
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        503: {
            "description": "Service not ready",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "SERVICE_NOT_READY",
                        "message": "Service is warming up, please try again",
                        "details": {},
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        }
    }
)
async def detect_features(
    image: UploadFile = File(
        ...,
        description="Image file to process (JPG, PNG, BMP, TIF/TIFF)",
        media_type="image/*"
    ),
    feature_service: FeatureService = Depends(get_feature_service),
    request_id: str = Depends(get_request_id)
) -> FeatureDetectionResponse:
    """
    Detect SIFT features in uploaded image.
    
    Args:
        image: Uploaded image file
        feature_service: Injected feature service
        request_id: Unique request identifier
    
    Returns:
        Feature detection results with metadata
    
    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/features/detect \
          -H "X-Request-ID: my-request-123" \
          -F "image=@/path/to/image.jpg"
        ```
        
        Response:
        ```json
        {
            "success": true,
            "keypoints": 1247,
            "descriptors_shape": [1247, 128],
            "cached": false,
            "processing_time_ms": 342.5,
            "request_id": "my-request-123"
        }
        ```
    """
    logger.info(
        "Feature detection request received",
        request_id=request_id,
        filename=image.filename,
        content_type=image.content_type
    )
    
    # Process image
    result = await feature_service.detect_features(image, request_id)
    
    # Build response
    response = FeatureDetectionResponse(
        keypoints=result["keypoints"],
        descriptors_shape=tuple(result["descriptors_shape"]),
        cached=result["cached"],
        processing_time_ms=result["processing_time_ms"],
        request_id=request_id
    )
    
    logger.info(
        "Feature detection request completed",
        request_id=request_id,
        keypoints=response.keypoints,
        cached=response.cached,
        processing_time_ms=response.processing_time_ms
    )
    
    return response

