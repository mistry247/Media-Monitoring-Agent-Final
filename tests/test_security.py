"""
Tests for security utilities and validation
"""
import pytest
import time
from unittest.mock import Mock, patch

from utils.security import (
    URLValidator,
    InputSanitizer,
    RateLimiter,
    CSRFProtection,
    SecurityHeaders,
    validate_and_sanitize_url,
    validate_and_sanitize_text,
    validate_and_sanitize_name,
    check_rate_limit,
    get_client_id,
    InvalidInputError,
    RateLimitExceeded,
    SecurityError
)

class TestURLValidator:
    """Test URL validation and sanitization"""
    
    def test_valid_http_url(self):
        """Test valid HTTP URL"""
        is_valid, sanitized, error = URLValidator.validate_url("http://example.com")
        assert is_valid is True
        assert sanitized == "http://example.com"
        assert error is None
    
    def test_valid_https_url(self):
        """Test valid HTTPS URL"""
        is_valid, sanitized, error = URLValidator.validate_url("https://example.com/path?query=value")
        assert is_valid is True
        assert sanitized == "https://example.com/path?query=value"
        assert error is None
    
    def test_url_case_normalization(self):
        """Test URL case normalization"""
        is_valid, sanitized, error = URLValidator.validate_url("HTTPS://EXAMPLE.COM/Path")
        assert is_valid is True
        assert sanitized == "https://example.com/Path"
        assert error is None
    
    def test_fragment_removal(self):
        """Test fragment removal for security"""
        is_valid, sanitized, error = URLValidator.validate_url("https://example.com/page#fragment")
        assert is_valid is True
        assert sanitized == "https://example.com/page"
        assert error is None
    
    def test_empty_url(self):
        """Test empty URL"""
        is_valid, sanitized, error = URLValidator.validate_url("")
        assert is_valid is False
        assert sanitized == ""
        assert "cannot be empty" in error
    
    def test_none_url(self):
        """Test None URL"""
        is_valid, sanitized, error = URLValidator.validate_url(None)
        assert is_valid is False
        assert sanitized == ""
        assert "cannot be empty" in error
    
    def test_invalid_scheme(self):
        """Test invalid URL scheme"""
        is_valid, sanitized, error = URLValidator.validate_url("ftp://example.com")
        assert is_valid is False
        assert "suspicious content" in error
    
    def test_javascript_scheme(self):
        """Test JavaScript scheme (security risk)"""
        is_valid, sanitized, error = URLValidator.validate_url("javascript:alert('xss')")
        assert is_valid is False
        assert "suspicious content" in error
    
    def test_data_scheme(self):
        """Test data scheme (security risk)"""
        is_valid, sanitized, error = URLValidator.validate_url("data:text/html,<script>alert('xss')</script>")
        assert is_valid is False
        assert "suspicious content" in error
    
    def test_script_tags(self):
        """Test URLs containing script tags"""
        is_valid, sanitized, error = URLValidator.validate_url("https://example.com/<script>alert('xss')</script>")
        assert is_valid is False
        assert "suspicious content" in error
    
    def test_long_url(self):
        """Test URL exceeding maximum length"""
        long_url = "https://example.com/" + "a" * 2050
        is_valid, sanitized, error = URLValidator.validate_url(long_url)
        assert is_valid is False
        assert "exceeds maximum length" in error
    
    def test_no_hostname(self):
        """Test URL without hostname"""
        is_valid, sanitized, error = URLValidator.validate_url("https://")
        assert is_valid is False
        assert "valid hostname" in error
    
    def test_blocked_domain(self):
        """Test blocked domain"""
        is_valid, sanitized, error = URLValidator.validate_url("https://localhost/test")
        assert is_valid is False
        assert "not allowed" in error
    
    def test_private_ip(self):
        """Test private IP address"""
        is_valid, sanitized, error = URLValidator.validate_url("https://192.168.1.1/test")
        assert is_valid is False
        assert "Private IP addresses are not allowed" in error

class TestInputSanitizer:
    """Test input sanitization"""
    
    def test_sanitize_normal_text(self):
        """Test normal text sanitization"""
        sanitized, error = InputSanitizer.sanitize_text("Hello world!")
        assert sanitized == "Hello world!"
        assert error is None
    
    def test_sanitize_html_content(self):
        """Test HTML content sanitization"""
        sanitized, error = InputSanitizer.sanitize_text("<script>alert('xss')</script>")
        assert sanitized == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        assert error is None
    
    def test_sanitize_long_text(self):
        """Test text exceeding maximum length"""
        long_text = "a" * 100001
        sanitized, error = InputSanitizer.sanitize_text(long_text)
        assert sanitized == ""
        assert "exceeds maximum length" in error
    
    def test_sanitize_non_string(self):
        """Test non-string input"""
        sanitized, error = InputSanitizer.sanitize_text(123)
        assert sanitized == ""
        assert "must be a string" in error
    
    def test_sanitize_name_valid(self):
        """Test valid name sanitization"""
        sanitized, error = InputSanitizer.sanitize_name("John Doe-Smith")
        assert sanitized == "John Doe-Smith"
        assert error is None
    
    def test_sanitize_name_with_apostrophe(self):
        """Test name with apostrophe"""
        sanitized, error = InputSanitizer.sanitize_name("O'Connor")
        assert sanitized == "O&#x27;Connor"
        assert error is None
    
    def test_sanitize_name_empty(self):
        """Test empty name"""
        sanitized, error = InputSanitizer.sanitize_name("")
        assert sanitized == ""
        assert "cannot be empty" in error
    
    def test_sanitize_name_invalid_chars(self):
        """Test name with invalid characters"""
        sanitized, error = InputSanitizer.sanitize_name("John@Doe")
        assert sanitized == ""
        assert "invalid characters" in error
    
    def test_sanitize_name_too_long(self):
        """Test name exceeding maximum length"""
        long_name = "a" * 101
        sanitized, error = InputSanitizer.sanitize_name(long_name)
        assert sanitized == ""
        assert "exceeds maximum length" in error

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests within limit"""
        limiter = RateLimiter()
        
        # Should allow first request
        is_allowed, info = limiter.is_allowed("client1", max_requests=5, window_seconds=60)
        assert is_allowed is True
        assert info["remaining"] == 4
        
        # Should allow subsequent requests
        is_allowed, info = limiter.is_allowed("client1", max_requests=5, window_seconds=60)
        assert is_allowed is True
        assert info["remaining"] == 3
    
    def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks requests exceeding limit"""
        limiter = RateLimiter()
        
        # Make requests up to limit
        for i in range(5):
            is_allowed, info = limiter.is_allowed("client2", max_requests=5, window_seconds=60)
            assert is_allowed is True
        
        # Next request should be blocked
        is_allowed, info = limiter.is_allowed("client2", max_requests=5, window_seconds=60)
        assert is_allowed is False
        assert info["remaining"] == 0
    
    def test_rate_limiter_different_clients(self):
        """Test rate limiter handles different clients separately"""
        limiter = RateLimiter()
        
        # Client 1 makes requests
        for i in range(5):
            is_allowed, info = limiter.is_allowed("client1", max_requests=5, window_seconds=60)
            assert is_allowed is True
        
        # Client 2 should still be allowed
        is_allowed, info = limiter.is_allowed("client2", max_requests=5, window_seconds=60)
        assert is_allowed is True
        assert info["remaining"] == 4
    
    def test_rate_limiter_window_expiry(self):
        """Test rate limiter window expiry"""
        limiter = RateLimiter()
        
        # Make requests up to limit
        for i in range(3):
            is_allowed, info = limiter.is_allowed("client3", max_requests=3, window_seconds=1)
            assert is_allowed is True
        
        # Should be blocked
        is_allowed, info = limiter.is_allowed("client3", max_requests=3, window_seconds=1)
        assert is_allowed is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        is_allowed, info = limiter.is_allowed("client3", max_requests=3, window_seconds=1)
        assert is_allowed is True

class TestCSRFProtection:
    """Test CSRF protection utilities"""
    
    def test_generate_token(self):
        """Test CSRF token generation"""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        
        assert len(token1) > 20  # Should be reasonably long
        assert len(token2) > 20
        assert token1 != token2  # Should be unique
    
    def test_validate_token_success(self):
        """Test successful token validation"""
        token = CSRFProtection.generate_token()
        assert CSRFProtection.validate_token(token, token) is True
    
    def test_validate_token_failure(self):
        """Test failed token validation"""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        assert CSRFProtection.validate_token(token1, token2) is False
    
    def test_validate_token_empty(self):
        """Test token validation with empty tokens"""
        assert CSRFProtection.validate_token("", "token") is False
        assert CSRFProtection.validate_token("token", "") is False
        assert CSRFProtection.validate_token("", "") is False

class TestSecurityHeaders:
    """Test security headers"""
    
    def test_get_security_headers(self):
        """Test security headers generation"""
        headers = SecurityHeaders.get_security_headers()
        
        # Check required security headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers
        
        # Check header values
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "max-age" in headers["Strict-Transport-Security"]

class TestSecurityFunctions:
    """Test high-level security functions"""
    
    def test_validate_and_sanitize_url_success(self):
        """Test successful URL validation"""
        result = validate_and_sanitize_url("https://example.com")
        assert result == "https://example.com"
    
    def test_validate_and_sanitize_url_failure(self):
        """Test URL validation failure"""
        with pytest.raises(InvalidInputError):
            validate_and_sanitize_url("javascript:alert('xss')")
    
    def test_validate_and_sanitize_text_success(self):
        """Test successful text validation"""
        result = validate_and_sanitize_text("Hello <world>!")
        assert result == "Hello &lt;world&gt;!"
    
    def test_validate_and_sanitize_text_failure(self):
        """Test text validation failure"""
        with pytest.raises(InvalidInputError):
            validate_and_sanitize_text("a" * 100001)
    
    def test_validate_and_sanitize_name_success(self):
        """Test successful name validation"""
        result = validate_and_sanitize_name("John Doe")
        assert result == "John Doe"
    
    def test_validate_and_sanitize_name_failure(self):
        """Test name validation failure"""
        with pytest.raises(InvalidInputError):
            validate_and_sanitize_name("John@Doe")
    
    @patch('utils.security.settings')
    def test_check_rate_limit_success(self, mock_settings):
        """Test successful rate limit check"""
        mock_settings.RATE_LIMIT_REQUESTS = 10
        mock_settings.RATE_LIMIT_WINDOW = 3600
        
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        
        result = check_rate_limit(mock_request)
        assert "limit" in result
        assert "remaining" in result
        assert "reset" in result
    
    @patch('utils.security.settings')
    @patch('utils.security.rate_limiter')
    def test_check_rate_limit_exceeded(self, mock_rate_limiter, mock_settings):
        """Test rate limit exceeded"""
        mock_settings.RATE_LIMIT_REQUESTS = 1
        mock_settings.RATE_LIMIT_WINDOW = 3600
        
        # Mock rate limiter to return exceeded limit
        mock_rate_limiter.is_allowed.return_value = (False, {
            "limit": 1,
            "remaining": 0,
            "reset": int(time.time()) + 3600,
            "window": 3600
        })
        
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.url.path = "/api/test"
        
        # Should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            check_rate_limit(mock_request)
    
    def test_get_client_id(self):
        """Test client ID generation"""
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "Mozilla/5.0"
        
        client_id = get_client_id(mock_request)
        assert "192.168.1.1:" in client_id
        assert len(client_id.split(":")) == 2
    
    def test_get_client_id_no_client(self):
        """Test client ID generation with no client info"""
        mock_request = Mock()
        mock_request.client = None
        mock_request.headers.get.return_value = "Mozilla/5.0"
        
        client_id = get_client_id(mock_request)
        assert "unknown:" in client_id

class TestSecurityExceptions:
    """Test security exception classes"""
    
    def test_security_error(self):
        """Test SecurityError exception"""
        with pytest.raises(SecurityError):
            raise SecurityError("Test error")
    
    def test_invalid_input_error(self):
        """Test InvalidInputError exception"""
        with pytest.raises(InvalidInputError):
            raise InvalidInputError("Invalid input")
    
    def test_rate_limit_exceeded(self):
        """Test RateLimitExceeded exception"""
        with pytest.raises(RateLimitExceeded):
            raise RateLimitExceeded("Rate limit exceeded")