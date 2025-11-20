"""
Custom exceptions for the Feature Detection API.
Provides specific error types for different failure scenarios.

Exception Hierarchy:
    FeatureDetectionException (Base)
    ├── ImageProcessingException
    │   ├── InvalidImageException
    │   ├── ImageTooLargeException
    │   └── ImageReadException
    ├── CacheException
    │   ├── CacheConnectionException
    │   └── CacheOperationException
    └── ServiceException
        ├── ServiceNotReadyException
        └── ServiceTimeoutException
"""

from typing import Any


class FeatureDetectionException(Exception):
    """
    Base exception for all feature detection errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code
        error_code: Machine-readable error code
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# Image Processing Exceptions
class ImageProcessingException(FeatureDetectionException):
    """Base class for image processing errors."""
    pass


class InvalidImageException(ImageProcessingException):
    """Raised when image format is invalid or corrupted."""
    
    def __init__(self, message: str = "Invalid image format", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_IMAGE",
            details=details
        )


class ImageTooLargeException(ImageProcessingException):
    """Raised when image exceeds size limit."""
    
    def __init__(self, size_mb: float, max_size_mb: int):
        super().__init__(
            message=f"Image size {size_mb:.2f}MB exceeds limit of {max_size_mb}MB",
            status_code=413,
            error_code="IMAGE_TOO_LARGE",
            details={"size_mb": size_mb, "max_size_mb": max_size_mb}
        )


class ImageReadException(ImageProcessingException):
    """Raised when image cannot be read."""
    
    def __init__(self, message: str = "Failed to read image"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="IMAGE_READ_ERROR"
        )


# Cache Exceptions
class CacheException(FeatureDetectionException):
    """Base class for cache-related errors."""
    pass


class CacheConnectionException(CacheException):
    """Raised when Redis connection fails."""
    
    def __init__(self, message: str = "Failed to connect to cache"):
        super().__init__(
            message=message,
            status_code=503,
            error_code="CACHE_CONNECTION_ERROR"
        )


class CacheOperationException(CacheException):
    """Raised when cache operation fails."""
    
    def __init__(self, operation: str, message: str = "Cache operation failed"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CACHE_OPERATION_ERROR",
            details={"operation": operation}
        )


# Service Exceptions
class ServiceException(FeatureDetectionException):
    """Base class for service-level errors."""
    pass


class ServiceNotReadyException(ServiceException):
    """Raised when service is not ready (warmup incomplete)."""
    
    def __init__(self, message: str = "Service is warming up, please try again"):
        super().__init__(
            message=message,
            status_code=503,
            error_code="SERVICE_NOT_READY"
        )


class ServiceTimeoutException(ServiceException):
    """Raised when operation times out."""
    
    def __init__(self, operation: str, timeout: int):
        super().__init__(
            message=f"{operation} timed out after {timeout}s",
            status_code=504,
            error_code="SERVICE_TIMEOUT",
            details={"operation": operation, "timeout_seconds": timeout}
        )

