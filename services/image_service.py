"""
Image validation and processing service.
Handles image file validation, size checks, and format verification.

Features:
- Async file operations
- Size validation
- Format validation
- Image hashing for cache keys
- Secure file handling

Example Usage:
    image_service = ImageService(settings)
    validated_path = await image_service.validate_and_save(upload_file)
    cache_key = await image_service.generate_cache_key(validated_path)
"""

import hashlib
import os
from pathlib import Path
from io import BytesIO

import aiofiles
from fastapi import UploadFile
from PIL import Image

from core.config import Settings
from core.logging_config import get_logger
from core.exceptions import (
    InvalidImageException,
    ImageTooLargeException,
    ImageReadException
)

logger = get_logger(__name__)


class ImageService:
    """
    Service for image validation and processing.
    
    Attributes:
        settings: Application settings
        upload_dir: Directory for temporary uploads
    
    Example:
        >>> service = ImageService(settings)
        >>> path = await service.validate_and_save(upload_file)
        >>> key = await service.generate_cache_key(path)
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize image service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_and_save(self, file: UploadFile) -> str:
        """
        Validate uploaded image and save to disk.
        
        Args:
            file: Uploaded image file
        
        Returns:
            Path to saved image file
        
        Raises:
            InvalidImageException: If image format is invalid
            ImageTooLargeException: If image exceeds size limit
            ImageReadException: If image cannot be read
        
        Example:
            >>> file = UploadFile(filename="test.jpg", file=...)
            >>> path = await service.validate_and_save(file)
            >>> print(path)  # "/app/data/uploads/abc123.jpg"
        """
        # Validate filename
        if not file.filename:
            raise InvalidImageException("No filename provided")
        
        # Validate extension
        extension = self._get_extension(file.filename)
        if extension not in self.settings.allowed_extensions:
            raise InvalidImageException(
                f"Invalid file extension: {extension}",
                details={"allowed": list(self.settings.allowed_extensions)}
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate size
        if file_size > self.settings.max_image_size_bytes:
            size_mb = file_size / (1024 * 1024)
            raise ImageTooLargeException(size_mb, self.settings.max_image_size_mb)
        
        # Validate it's actually an image using PIL
        try:
            img = Image.open(BytesIO(content))
            img.verify()  # Verify it's not corrupted
        except Exception as e:
            logger.warning("Image verification failed", filename=file.filename, error=str(e))
            raise InvalidImageException(f"Invalid or corrupted image: {e}")
        
        # Generate unique filename based on content hash
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        safe_filename = f"{file_hash}.{extension}"
        file_path = self.upload_dir / safe_filename
        
        # Save file asynchronously
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info(
                "Image saved",
                filename=file.filename,
                size_bytes=file_size,
                saved_path=str(file_path)
            )
            
            return str(file_path)
            
        except Exception as e:
            logger.error("Failed to save image", filename=file.filename, error=str(e))
            raise ImageReadException(f"Failed to save image: {e}")
    
    async def generate_cache_key(self, file_path: str) -> str:
        """
        Generate cache key from image file.
        Uses SHA256 hash of file content.
        
        Args:
            file_path: Path to image file
        
        Returns:
            Cache key string
        
        Example:
            >>> key = await service.generate_cache_key("/app/data/image.jpg")
            >>> print(key)  # "features:abc123def456..."
        """
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            file_hash = hashlib.sha256(content).hexdigest()
            cache_key = f"features:{file_hash}"
            
            logger.debug("Cache key generated", file_path=file_path, cache_key=cache_key)
            return cache_key
            
        except Exception as e:
            logger.error("Failed to generate cache key", file_path=file_path, error=str(e))
            # Return a fallback key based on file path
            return f"features:{hashlib.sha256(file_path.encode()).hexdigest()}"
    
    async def cleanup_file(self, file_path: str) -> None:
        """
        Delete temporary image file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("File cleaned up", file_path=file_path)
        except Exception as e:
            logger.warning("Failed to cleanup file", file_path=file_path, error=str(e))
    
    @staticmethod
    def _get_extension(filename: str) -> str:
        """
        Extract file extension from filename.
        
        Args:
            filename: Original filename
        
        Returns:
            Lowercase extension without dot
        """
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

