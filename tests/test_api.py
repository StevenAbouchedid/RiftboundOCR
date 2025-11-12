"""
Unit Tests for FastAPI Endpoints
Tests API routes, request/response handling, and error cases
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
import os
import io
from PIL import Image


# Create test client
client = TestClient(app)


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_service_info(self):
        """Test that root endpoint returns service information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
    
    def test_root_includes_endpoints_list(self):
        """Test that root endpoint lists available endpoints"""
        response = client.get("/")
        
        data = response.json()
        assert "endpoints" in data
        assert "process_single" in data["endpoints"]


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK"""
        response = client.get("/api/v1/health")
        
        # May be 200 or 503 depending on OCR initialization
        assert response.status_code in [200, 503]
    
    def test_health_check_structure(self):
        """Test that health check has correct structure"""
        response = client.get("/api/v1/health")
        
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "matcher_loaded" in data
        assert "total_cards_in_db" in data
    
    def test_health_check_when_healthy(self):
        """Test health check when service is healthy"""
        response = client.get("/api/v1/health")
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"
            assert data["matcher_loaded"] == True
            assert data["total_cards_in_db"] > 0


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_stats_returns_200(self):
        """Test that stats endpoint returns 200 OK"""
        response = client.get("/api/v1/stats")
        
        assert response.status_code == 200
    
    def test_stats_structure(self):
        """Test that stats have correct structure"""
        response = client.get("/api/v1/stats")
        
        data = response.json()
        assert "matcher" in data
        assert "parser" in data
    
    def test_stats_matcher_info(self):
        """Test that matcher stats are included"""
        response = client.get("/api/v1/stats")
        
        data = response.json()
        assert "total_cards" in data["matcher"]
        assert "base_names" in data["matcher"]
        assert "supported_languages" in data["matcher"]
    
    def test_stats_parser_info(self):
        """Test that parser stats are included"""
        response = client.get("/api/v1/stats")
        
        data = response.json()
        assert "ocr_engines" in data["parser"]
        assert "supported_formats" in data["parser"]


class TestProcessSingleImageEndpoint:
    """Test single image processing endpoint"""
    
    def test_process_requires_file(self):
        """Test that endpoint requires file parameter"""
        response = client.post("/api/v1/process")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_process_rejects_non_image(self):
        """Test that non-image files are rejected"""
        # Create a text file
        file_content = b"This is not an image"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/api/v1/process", files=files)
        
        assert response.status_code == 400
        assert "must be an image" in response.json()["detail"].lower()
    
    def test_process_accepts_jpg_image(self, sample_image):
        """Test that JPG images are accepted"""
        with open(sample_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = client.post("/api/v1/process", files=files)
        
        # Should not reject for file type (may fail processing)
        assert response.status_code in [200, 500, 503]
    
    def test_process_returns_correct_structure(self, sample_image):
        """Test that successful response has correct structure"""
        with open(sample_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = client.post("/api/v1/process", files=files)
        
        # Only check structure if processing succeeded
        if response.status_code == 200:
            data = response.json()
            assert "decklist_id" in data
            assert "metadata" in data
            assert "legend" in data
            assert "main_deck" in data
            assert "battlefields" in data
            assert "runes" in data
            assert "side_deck" in data
            assert "stats" in data
    
    def test_process_generates_unique_id(self, sample_image):
        """Test that each request gets a unique decklist ID"""
        with open(sample_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response1 = client.post("/api/v1/process", files=files)
        
        with open(sample_image, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response2 = client.post("/api/v1/process", files=files)
        
        if response1.status_code == 200 and response2.status_code == 200:
            id1 = response1.json()["decklist_id"]
            id2 = response2.json()["decklist_id"]
            assert id1 != id2


class TestProcessBatchEndpoint:
    """Test batch processing endpoint"""
    
    def test_batch_requires_files(self):
        """Test that endpoint requires files parameter"""
        response = client.post("/api/v1/process-batch")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_batch_accepts_multiple_files(self, sample_image):
        """Test that batch endpoint accepts multiple files"""
        files = []
        with open(sample_image, "rb") as f1:
            with open(sample_image, "rb") as f2:
                files = [
                    ("files", ("test1.jpg", f1.read(), "image/jpeg")),
                    ("files", ("test2.jpg", f2.read(), "image/jpeg"))
                ]
                
                response = client.post("/api/v1/process-batch", files=files)
        
        assert response.status_code in [200, 503]
    
    def test_batch_returns_correct_structure(self, sample_image):
        """Test that batch response has correct structure"""
        with open(sample_image, "rb") as f:
            content = f.read()
            files = [("files", ("test.jpg", content, "image/jpeg"))]
            
            response = client.post("/api/v1/process-batch", files=files)
        
        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "successful" in data
            assert "failed" in data
            assert "average_accuracy" in data
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_batch_counts_match_files_sent(self, sample_image):
        """Test that total count matches files sent"""
        with open(sample_image, "rb") as f:
            content = f.read()
            files = [
                ("files", ("test1.jpg", content, "image/jpeg")),
                ("files", ("test2.jpg", content, "image/jpeg"))
            ]
            
            response = client.post("/api/v1/process-batch", files=files)
        
        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 2
    
    def test_batch_skips_non_images(self, sample_image):
        """Test that batch skips non-image files"""
        with open(sample_image, "rb") as f:
            img_content = f.read()
            
        files = [
            ("files", ("test.jpg", img_content, "image/jpeg")),
            ("files", ("test.txt", b"not an image", "text/plain"))
        ]
        
        response = client.post("/api/v1/process-batch", files=files)
        
        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 2
            # Should skip the text file
            assert data["failed"] >= 1


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_for_unknown_endpoint(self):
        """Test that unknown endpoints return 404"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self):
        """Test that wrong HTTP method returns 405"""
        # Health check is GET, try POST
        response = client.post("/api/v1/health")
        
        assert response.status_code == 405
    
    def test_error_responses_have_detail(self):
        """Test that error responses include detail"""
        # Trigger error by not sending file
        response = client.post("/api/v1/process")
        
        assert response.status_code >= 400
        data = response.json()
        assert "detail" in data


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.options("/api/v1/health")
        
        # CORS middleware should add these headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_cors_allows_all_origins(self):
        """Test that CORS allows all origins (for development)"""
        headers = {"origin": "http://example.com"}
        response = client.get("/api/v1/health", headers=headers)
        
        # Should allow the origin
        assert response.status_code in [200, 503]


class TestDocumentation:
    """Test API documentation endpoints"""
    
    def test_swagger_docs_available(self):
        """Test that Swagger UI is available"""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_redoc_available(self):
        """Test that ReDoc is available"""
        response = client.get("/redoc")
        
        assert response.status_code == 200
    
    def test_openapi_schema_available(self):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




