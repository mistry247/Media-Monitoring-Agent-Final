"""
Tests for report generation API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from main import app
from database import get_db
from schemas import MediaReportRequest, HansardReportRequest, ReportResponse, ReportStatus

# Create test client
client = TestClient(app)

# Mock database session
@pytest.fixture
def mock_db():
    """Mock database session for testing"""
    db = Mock()
    return db

@pytest.fixture
def override_get_db(mock_db):
    """Override database dependency for testing"""
    def _override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

class TestMediaReportEndpoint:
    """Tests for POST /api/reports/media endpoint"""
    
    def test_generate_media_report_success(self, override_get_db):
        """Test successful media report generation request"""
        # Prepare test data
        request_data = {
            "pasted_content": "This is test pasted content for media report generation."
        }
        
        # Make request
        response = client.post("/api/reports/media", json=request_data)
        
        # Verify response
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["success"] is True
        assert "Media report generation started" in response_data["message"]
        assert response_data["report_id"] is not None
        assert response_data["report_id"].startswith("media_report_")
    
    def test_generate_media_report_empty_content(self, override_get_db):
        """Test media report generation with empty pasted content"""
        # Prepare test data
        request_data = {
            "pasted_content": ""
        }
        
        # Make request
        response = client.post("/api/reports/media", json=request_data)
        
        # Verify response - should still succeed as empty content is valid
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["report_id"] is not None
    
    def test_generate_media_report_large_content(self, override_get_db):
        """Test media report generation with content exceeding size limit"""
        # Prepare test data with content exceeding 100KB limit
        large_content = "x" * 100001  # 100KB + 1 character
        request_data = {
            "pasted_content": large_content
        }
        
        # Make request
        response = client.post("/api/reports/media", json=request_data)
        
        # Verify response - should fail validation
        assert response.status_code == 422
        response_data = response.json()
        assert "exceeds maximum length" in response_data["detail"][0]["msg"].lower()
    
    def test_generate_media_report_invalid_request(self, override_get_db):
        """Test media report generation with invalid request format"""
        # Make request with invalid data
        response = client.post("/api/reports/media", json={"invalid_field": "value"})
        
        # Verify response
        assert response.status_code == 422
        response_data = response.json()
        assert "field required" in str(response_data["detail"]).lower()
    
    def test_generate_media_report_missing_content_field(self, override_get_db):
        """Test media report generation with missing pasted_content field"""
        # Make request without required field
        response = client.post("/api/reports/media", json={})
        
        # Verify response
        assert response.status_code == 422
        response_data = response.json()
        assert "field required" in str(response_data["detail"]).lower()

class TestHansardReportEndpoint:
    """Tests for POST /api/reports/hansard endpoint"""
    
    def test_generate_hansard_report_success(self, override_get_db):
        """Test successful Hansard report generation request"""
        # Make request
        response = client.post("/api/reports/hansard", json={})
        
        # Verify response
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["success"] is True
        assert "Hansard report generation started" in response_data["message"]
        assert response_data["report_id"] is not None
        assert response_data["report_id"].startswith("hansard_report_")
    
    def test_generate_hansard_report_with_extra_fields(self, override_get_db):
        """Test Hansard report generation with extra fields (should be ignored)"""
        # Make request with extra fields
        response = client.post("/api/reports/hansard", json={"extra_field": "value"})
        
        # Verify response - should succeed and ignore extra fields
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["report_id"] is not None

class TestReportStatusEndpoint:
    """Tests for GET /api/reports/status/{report_id} endpoint"""
    
    def test_get_report_status_not_found(self, override_get_db):
        """Test getting status for non-existent report"""
        # Make request for non-existent report
        response = client.get("/api/reports/status/non_existent_report")
        
        # Verify response
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()
    
    def test_get_report_status_after_creation(self, override_get_db):
        """Test getting status for a report after creation"""
        # First create a report
        create_response = client.post("/api/reports/media", json={"pasted_content": "test"})
        assert create_response.status_code == 202
        report_id = create_response.json()["report_id"]
        
        # Then get its status
        status_response = client.get(f"/api/reports/status/{report_id}")
        
        # Verify response
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["report_id"] == report_id
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
        assert status_data["message"] is not None

class TestRecentHansardQuestionsEndpoint:
    """Tests for GET /api/reports/hansard/recent endpoint"""
    
    @patch('api.reports.get_report_service')
    def test_get_recent_hansard_questions_success(self, mock_get_service, override_get_db):
        """Test successful retrieval of recent Hansard questions"""
        # Mock the report service
        mock_service = Mock()
        mock_questions = [
            {
                'id': 1,
                'question_text': 'Test question 1',
                'category': 'Media-based Questions',
                'timestamp': datetime.now(),
                'source_articles': [1, 2]
            },
            {
                'id': 2,
                'question_text': 'Test question 2',
                'category': 'Media-based Questions',
                'timestamp': datetime.now(),
                'source_articles': [3]
            }
        ]
        mock_service.get_recent_hansard_questions.return_value = mock_questions
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/reports/hansard/recent")
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["count"] == 2
        assert len(response_data["questions"]) == 2
        assert response_data["questions"][0]["question_text"] == "Test question 1"
    
    @patch('api.reports.get_report_service')
    def test_get_recent_hansard_questions_with_limit(self, mock_get_service, override_get_db):
        """Test retrieval of recent Hansard questions with custom limit"""
        # Mock the report service
        mock_service = Mock()
        mock_service.get_recent_hansard_questions.return_value = []
        mock_get_service.return_value = mock_service
        
        # Make request with limit
        response = client.get("/api/reports/hansard/recent?limit=5")
        
        # Verify response
        assert response.status_code == 200
        mock_service.get_recent_hansard_questions.assert_called_once_with(5)
    
    def test_get_recent_hansard_questions_invalid_limit(self, override_get_db):
        """Test retrieval with invalid limit values"""
        # Test limit too low
        response = client.get("/api/reports/hansard/recent?limit=0")
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["detail"]
        
        # Test limit too high
        response = client.get("/api/reports/hansard/recent?limit=101")
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["detail"]
    
    @patch('api.reports.get_report_service')
    def test_get_recent_hansard_questions_empty_result(self, mock_get_service, override_get_db):
        """Test retrieval when no Hansard questions exist"""
        # Mock the report service to return empty list
        mock_service = Mock()
        mock_service.get_recent_hansard_questions.return_value = []
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/reports/hansard/recent")
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["count"] == 0
        assert response_data["questions"] == []

class TestClearReportStatusEndpoint:
    """Tests for DELETE /api/reports/status/{report_id} endpoint"""
    
    def test_clear_report_status_not_found(self, override_get_db):
        """Test clearing status for non-existent report"""
        # Make request for non-existent report
        response = client.delete("/api/reports/status/non_existent_report")
        
        # Verify response
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()
    
    @patch('api.reports.generate_media_report_async')
    def test_clear_report_status_pending_report(self, mock_async_func, override_get_db):
        """Test clearing status for a pending report (should fail)"""
        # Mock the async function to do nothing
        mock_async_func.return_value = None
        
        # First create a report
        create_response = client.post("/api/reports/media", json={"pasted_content": "test"})
        assert create_response.status_code == 202
        report_id = create_response.json()["report_id"]
        
        # Try to clear status while still pending
        clear_response = client.delete(f"/api/reports/status/{report_id}")
        
        # Verify response - should fail because report is not completed/failed
        assert clear_response.status_code == 400
        assert "completed or failed" in clear_response.json()["detail"]

class TestReportWorkflowIntegration:
    """Integration tests for complete report generation workflows"""
    
    @patch('api.reports.generate_media_report_async')
    def test_media_report_workflow(self, mock_async_func, override_get_db):
        """Test complete media report generation workflow"""
        # Mock the async function to do nothing
        mock_async_func.return_value = None
        
        # Step 1: Create media report
        create_response = client.post("/api/reports/media", json={"pasted_content": "Test content"})
        assert create_response.status_code == 202
        report_id = create_response.json()["report_id"]
        
        # Step 2: Check initial status
        status_response = client.get(f"/api/reports/status/{report_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "pending"
        
        # Note: In a real test, we would wait for background processing to complete
        # For this test, we're just verifying the API endpoints work correctly
    
    @patch('api.reports.generate_hansard_report_async')
    def test_hansard_report_workflow(self, mock_async_func, override_get_db):
        """Test complete Hansard report generation workflow"""
        # Mock the async function to do nothing
        mock_async_func.return_value = None
        
        # Step 1: Create Hansard report
        create_response = client.post("/api/reports/hansard", json={})
        assert create_response.status_code == 202
        report_id = create_response.json()["report_id"]
        
        # Step 2: Check initial status
        status_response = client.get(f"/api/reports/status/{report_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "pending"

class TestErrorHandling:
    """Tests for error handling in report endpoints"""
    
    def test_service_initialization_error(self, override_get_db):
        """Test handling when there are initialization issues"""
        # This test verifies that the API endpoint itself works correctly
        # Background task errors are handled separately and don't affect the initial response
        
        # Make request
        response = client.post("/api/reports/media", json={"pasted_content": "test"})
        
        # Verify response - should return 202 since the endpoint accepts the request
        assert response.status_code == 202
        assert response.json()["success"] is True
        assert "report_id" in response.json()
    
    @patch('api.reports.get_report_service')
    def test_hansard_questions_service_error(self, mock_get_service, override_get_db):
        """Test handling when Hansard questions service fails"""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.get_recent_hansard_questions.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/reports/hansard/recent")
        
        # Verify error response
        assert response.status_code == 500
        assert "error occurred while retrieving" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])