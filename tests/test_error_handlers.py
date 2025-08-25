"""
Tests for error handling utilities
"""
import pytest
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError

from utils.error_handlers import (
    MediaMonitoringError,
    ArticleServiceError,
    ScrapingServiceError,
    AIServiceError,
    EmailServiceError,
    ReportServiceError,
    DatabaseError,
    ConfigurationError,
    ExternalServiceError,
    create_error_response,
    handle_database_error,
    handle_validation_error,
    handle_service_error,
    handle_generic_error,
    safe_execute
)

class TestMediaMonitoringError:
    """Test custom exception classes"""
    
    def test_base_exception_creation(self):
        """Test base MediaMonitoringError creation"""
        error = MediaMonitoringError("Test message", "TEST_CODE", {"key": "value"})
        
        assert error.message == "Test message"
        assert error.error_code == "TEST_CODE"
        assert error.details == {"key": "value"}
        assert str(error) == "Test message"
    
    def test_base_exception_defaults(self):
        """Test base MediaMonitoringError with defaults"""
        error = MediaMonitoringError("Test message")
        
        assert error.message == "Test message"
        assert error.error_code == "MediaMonitoringError"
        assert error.details == {}
    
    def test_service_specific_exceptions(self):
        """Test service-specific exception classes"""
        exceptions = [
            ArticleServiceError,
            ScrapingServiceError,
            AIServiceError,
            EmailServiceError,
            ReportServiceError,
            DatabaseError,
            ConfigurationError,
            ExternalServiceError
        ]
        
        for exc_class in exceptions:
            error = exc_class("Test message")
            assert isinstance(error, MediaMonitoringError)
            assert error.message == "Test message"

class TestErrorResponseCreation:
    """Test error response creation"""
    
    def test_create_basic_error_response(self):
        """Test creating basic error response"""
        response = create_error_response(
            "TEST_ERROR",
            "Test message",
            400
        )
        
        expected = {
            "success": False,
            "error": {
                "code": "TEST_ERROR",
                "message": "Test message",
                "status_code": 400
            }
        }
        
        assert response == expected
    
    def test_create_error_response_with_details(self):
        """Test creating error response with details"""
        details = {"field": "value", "count": 5}
        response = create_error_response(
            "TEST_ERROR",
            "Test message",
            400,
            details=details
        )
        
        assert response["error"]["details"] == details
    
    def test_create_error_response_with_request_id(self):
        """Test creating error response with request ID"""
        response = create_error_response(
            "TEST_ERROR",
            "Test message",
            400,
            request_id="test-request-123"
        )
        
        assert response["error"]["request_id"] == "test-request-123"

class TestDatabaseErrorHandling:
    """Test database error handling"""
    
    def test_handle_integrity_error_unique_constraint(self):
        """Test handling unique constraint violation"""
        error = IntegrityError("statement", "params", "UNIQUE constraint failed: table.column")
        
        http_exception = handle_database_error(error, "test operation")
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_409_CONFLICT
        assert "DUPLICATE_ENTRY" in str(http_exception.detail)
    
    def test_handle_integrity_error_other(self):
        """Test handling other integrity errors"""
        error = IntegrityError("statement", "params", "NOT NULL constraint failed")
        
        http_exception = handle_database_error(error, "test operation")
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_400_BAD_REQUEST
        assert "DATA_INTEGRITY_ERROR" in str(http_exception.detail)
    
    def test_handle_sqlalchemy_error(self):
        """Test handling generic SQLAlchemy errors"""
        error = SQLAlchemyError("Database connection failed")
        
        http_exception = handle_database_error(error, "test operation")
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "DATABASE_ERROR" in str(http_exception.detail)
    
    def test_handle_unknown_database_error(self):
        """Test handling unknown database errors"""
        error = Exception("Unknown error")
        
        http_exception = handle_database_error(error, "test operation")
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "UNKNOWN_DATABASE_ERROR" in str(http_exception.detail)

class TestServiceErrorHandling:
    """Test service error handling"""
    
    def test_handle_article_service_error(self):
        """Test handling ArticleServiceError"""
        error = ArticleServiceError("Article not found", "ARTICLE_NOT_FOUND")
        
        http_exception = handle_service_error(error)
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_400_BAD_REQUEST
        assert "ARTICLE_NOT_FOUND" in str(http_exception.detail)
    
    def test_handle_external_service_error(self):
        """Test handling ExternalServiceError"""
        error = ExternalServiceError("API unavailable", "API_UNAVAILABLE")
        
        http_exception = handle_service_error(error)
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_502_BAD_GATEWAY
        assert "API_UNAVAILABLE" in str(http_exception.detail)
    
    def test_handle_configuration_error(self):
        """Test handling ConfigurationError"""
        error = ConfigurationError("Missing API key", "MISSING_API_KEY")
        
        http_exception = handle_service_error(error)
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "MISSING_API_KEY" in str(http_exception.detail)

class TestGenericErrorHandling:
    """Test generic error handling"""
    
    def test_handle_generic_error(self):
        """Test handling generic exceptions"""
        error = ValueError("Invalid value")
        
        http_exception = handle_generic_error(error, "test operation")
        
        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "INTERNAL_SERVER_ERROR" in str(http_exception.detail)

class TestSafeExecute:
    """Test safe execution wrapper"""
    
    def test_safe_execute_success(self):
        """Test successful execution"""
        def test_func():
            return "success"
        
        result = safe_execute(test_func)
        assert result == "success"
    
    def test_safe_execute_service_error(self):
        """Test safe execution with service error"""
        def test_func():
            raise ArticleServiceError("Test error", "TEST_ERROR")
        
        with pytest.raises(HTTPException) as exc_info:
            safe_execute(test_func)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_safe_execute_database_error(self):
        """Test safe execution with database error"""
        def test_func():
            raise IntegrityError("statement", "params", "UNIQUE constraint failed")
        
        with pytest.raises(HTTPException) as exc_info:
            safe_execute(test_func, operation="test operation")
        
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    
    def test_safe_execute_generic_error(self):
        """Test safe execution with generic error"""
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(HTTPException) as exc_info:
            safe_execute(test_func, operation="test operation")
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_safe_execute_with_custom_error_handler(self):
        """Test safe execution with custom error handler"""
        def test_func():
            raise ValueError("Test error")
        
        def custom_handler(error):
            return f"Custom: {str(error)}"
        
        result = safe_execute(test_func, error_handler=custom_handler)
        assert result == "Custom: Test error"