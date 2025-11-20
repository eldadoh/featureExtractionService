"""
Integration tests for API endpoints.
Tests complete request/response flow.
"""

import pytest
from io import BytesIO
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns API info."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
    
    def test_health_endpoint(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        # May fail if Redis not available in test
        assert response.status_code in [200, 503]
    
    def test_liveness_probe(self, test_client: TestClient):
        """Test liveness probe endpoint."""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_openapi_docs(self, test_client: TestClient):
        """Test OpenAPI documentation is accessible."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/v1/features/detect" in data["paths"]

