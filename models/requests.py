"""
Pydantic models for API request validation.
Ensures type safety and content validation.

Models:
    - FeatureDetectionRequest: Request to detect features in an image
"""

from pydantic import BaseModel


class FeatureDetectionRequest(BaseModel):
    """
    Request model for feature detection.
    
    Attributes:
        image: Uploaded image file
    
    Example:
        Request (multipart/form-data):
        {
            "image": <binary image data>
        }
    """
    
    # Note: UploadFile validation happens in the route
    # This model is for documentation purposes
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Feature detection request",
                    "content": {
                        "multipart/form-data": {
                            "image": "barbara.bmp (binary)"
                        }
                    }
                }
            ]
        }
    }

