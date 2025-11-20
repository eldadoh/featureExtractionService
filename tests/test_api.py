"""
Simple API integration tests.
"""
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Set up test environment before importing app
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["ENVIRONMENT"] = "development"

from api.main import app


class TestAPI:
    """Simple API tests."""

    
    def test_health_endpoint(self):
        """Test health endpoint."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code in [200, 503]
    
    def test_detect_endpoint(self):
        """Test detect endpoint with image."""
        client = TestClient(app)
        
        image_path = Path("data/images/lena_color_256.tif")
        if not image_path.exists():
            return
        
        with open(image_path, 'rb') as f:
            response = client.post(
                "/api/v1/features/detect",
                files={"image": (image_path.name, f, "image/tiff")}
            )
        
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "keypoints" in data


