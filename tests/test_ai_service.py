"""
Unit tests for AI service
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from services.ai_service import AIService, GeminiAPIClient, RateLimiter, SummaryResult, get_ai_service

class TestRateLimiter:
    """Test cases for RateLimiter class"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(max_requests_per_minute=10)
        assert limiter.max_requests == 10
        assert limiter.requests == []
    
    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that rate limiter allows requests under the limit"""
        limiter = RateLimiter(max_requests_per_minute=5)
        
        # Should not block for requests under limit
        start_time = time.time()
        for _ in range(3):
            limiter.wait_if_needed()
        end_time = time.time()
        
        # Should complete quickly (no significant waiting)
        assert end_time - start_time < 1.0
        assert len(limiter.requests) == 3
    
    @patch('time.sleep')
    def test_rate_limiter_blocks_when_limit_exceeded(self, mock_sleep):
        """Test that rate limiter blocks when limit is exceeded"""
        limiter = RateLimiter(max_requests_per_minute=2)
        
        # Fill up the rate limiter
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        
        # This should trigger rate limiting
        limiter.wait_if_needed()
        
        # Should have called sleep
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] > 0  # Sleep time should be positive

class TestSummaryResult:
    """Test cases for SummaryResult dataclass"""
    
    def test_summary_result_success(self):
        """Test successful SummaryResult creation"""
        result = SummaryResult(success=True, content="Test summary", tokens_used=100)
        assert result.success is True
        assert result.content == "Test summary"
        assert result.error is None
        assert result.tokens_used == 100
    
    def test_summary_result_failure(self):
        """Test failed SummaryResult creation"""
        result = SummaryResult(success=False, error="API error")
        assert result.success is False
        assert result.content is None
        assert result.error == "API error"
        assert result.tokens_used is None

class TestClaudeAPIClient:
    """Test cases for ClaudeAPIClient class"""
    
    def test_client_initialization(self):
        """Test Claude API client initialization"""
        client = ClaudeAPIClient("test-api-key")
        assert client.api_key == "test-api-key"
        assert client.api_url == "https://api.anthropic.com/v1/messages"
        assert client.rate_limiter is not None
        assert client.session is not None
    
    def test_client_initialization_with_custom_url(self):
        """Test Claude API client initialization with custom URL"""
        custom_url = "https://custom-api.example.com/v1/messages"
        client = ClaudeAPIClient("test-api-key", custom_url)
        assert client.api_url == custom_url
    
    @patch('requests.Session.post')
    def test_make_request_success(self, mock_post):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"text": "Test summary"}],
            "usage": {"output_tokens": 50}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = ClaudeAPIClient("test-api-key")
        result = client._make_request("Test content")
        
        assert result == {
            "content": [{"text": "Test summary"}],
            "usage": {"output_tokens": 50}
        }
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['messages'][0]['content'] == "Test content"
        assert call_args[1]['headers']['x-api-key'] == "test-api-key"
    
    @patch('requests.Session.post')
    def test_make_request_http_error(self, mock_post):
        """Test API request with HTTP error"""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("HTTP 429 Error")
        mock_post.return_value = mock_response
        
        client = ClaudeAPIClient("test-api-key")
        
        with pytest.raises(HTTPError):
            client._make_request("Test content")
    
    @patch('requests.Session.post')
    def test_make_request_timeout(self, mock_post):
        """Test API request with timeout"""
        mock_post.side_effect = Timeout("Request timeout")
        
        client = ClaudeAPIClient("test-api-key")
        
        with pytest.raises(Timeout):
            client._make_request("Test content")
    
    @patch('requests.Session.post')
    def test_summarize_success(self, mock_post):
        """Test successful content summarization"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"text": "This is a test summary of the content."}],
            "usage": {"output_tokens": 75}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = ClaudeAPIClient("test-api-key")
        result = client.summarize("Test article content")
        
        assert result.success is True
        assert result.content == "This is a test summary of the content."
        assert result.tokens_used == 75
        assert result.error is None
    
    @patch('requests.Session.post')
    def test_summarize_empty_content(self, mock_post):
        """Test summarization with empty content"""
        client = ClaudeAPIClient("test-api-key")
        result = client.summarize("")
        
        assert result.success is False
        assert result.error == "Empty content provided"
        assert result.content is None
        # Should not make API call for empty content
        mock_post.assert_not_called()
    
    @patch('requests.Session.post')
    def test_summarize_http_401_error(self, mock_post):
        """Test summarization with authentication error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = HTTPError("HTTP 401 Error", response=mock_response)
        mock_post.return_value = mock_response
        
        client = ClaudeAPIClient("test-api-key")
        result = client.summarize("Test content")
        
        assert result.success is False
        assert result.error == "Authentication failed - check API key"
        assert result.content is None
    
    @patch('requests.Session.post')
    def test_summarize_http_429_error(self, mock_post):
        """Test summarization with rate limit error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = HTTPError("HTTP 429 Error", response=mock_response)
        mock_post.return_value = mock_response
        
        client = ClaudeAPIClient("test-api-key")
        result = client.summarize("Test content")
        
        assert result.success is False
        assert result.error == "Rate limit exceeded"
        assert result.content is None
    
    @patch('requests.Session.post')
    def test_summarize_network_error(self, mock_post):
        """Test summarization with network error"""
        mock_post.side_effect = RequestException("Network error")
        
        client = ClaudeAPIClient("test-api-key")
        result = client.summarize("Test content")
        
        assert result.success is False
        assert "Network error" in result.error
        assert result.content is None
    
    def test_create_media_summary_prompt(self):
        """Test media summary prompt creation"""
        client = ClaudeAPIClient("test-api-key")
        prompt = client._create_media_summary_prompt("Test article content")
        
        assert "media content" in prompt
        assert "political monitoring report" in prompt
        assert "Test article content" in prompt
    
    def test_create_hansard_summary_prompt(self):
        """Test Hansard summary prompt creation"""
        client = ClaudeAPIClient("test-api-key")
        prompt = client._create_hansard_summary_prompt("Test article content")
        
        assert "parliamentary questions" in prompt
        assert "Hansard" in prompt
        assert "Test article content" in prompt

class TestAIService:
    """Test cases for AIService class"""
    
    def test_service_initialization_success(self):
        """Test successful AI service initialization"""
        service = AIService("test-api-key")
        assert service.client is not None
        assert service.client.api_key == "test-api-key"
    
    def test_service_initialization_no_api_key(self):
        """Test AI service initialization without API key"""
        with pytest.raises(ValueError, match="Claude API key is required"):
            AIService("")
        
        with pytest.raises(ValueError, match="Claude API key is required"):
            AIService(None)
    
    @patch('services.ai_service.ClaudeAPIClient.summarize')
    def test_summarize_content_success(self, mock_summarize):
        """Test successful content summarization"""
        mock_summarize.return_value = SummaryResult(
            success=True,
            content="Test summary",
            tokens_used=100
        )
        
        service = AIService("test-api-key")
        result = service.summarize_content("Test article content")
        
        assert result.success is True
        assert result.content == "Test summary"
        assert result.tokens_used == 100
        mock_summarize.assert_called_once_with("Test article content", "media")
    
    def test_summarize_content_empty_input(self):
        """Test content summarization with empty input"""
        service = AIService("test-api-key")
        
        # Test empty string
        result = service.summarize_content("")
        assert result.success is False
        assert result.error == "No content provided"
        
        # Test whitespace only
        result = service.summarize_content("   ")
        assert result.success is False
        assert result.error == "No content provided"
        
        # Test None
        result = service.summarize_content(None)
        assert result.success is False
        assert result.error == "No content provided"
    
    @patch('services.ai_service.ClaudeAPIClient.summarize')
    def test_summarize_content_truncation(self, mock_summarize):
        """Test content truncation for long content"""
        mock_summarize.return_value = SummaryResult(success=True, content="Summary")
        
        service = AIService("test-api-key")
        long_content = "x" * 150000  # Longer than max_chars limit
        
        result = service.summarize_content(long_content)
        
        # Should still succeed but content should be truncated
        assert result.success is True
        mock_summarize.assert_called_once()
        
        # Check that the content passed to summarize was truncated
        called_content = mock_summarize.call_args[0][0]
        assert len(called_content) <= 100050  # max_chars + truncation message
        assert "[Content truncated due to length]" in called_content
    
    @patch('services.ai_service.ClaudeAPIClient.summarize')
    def test_summarize_content_hansard_type(self, mock_summarize):
        """Test content summarization with Hansard type"""
        mock_summarize.return_value = SummaryResult(success=True, content="Hansard summary")
        
        service = AIService("test-api-key")
        result = service.summarize_content("Test content", "hansard")
        
        assert result.success is True
        mock_summarize.assert_called_once_with("Test content", "hansard")
    
    @patch('time.sleep')
    @patch('services.ai_service.ClaudeAPIClient.summarize')
    def test_batch_summarize_success(self, mock_summarize, mock_sleep):
        """Test successful batch summarization"""
        mock_summarize.side_effect = [
            SummaryResult(success=True, content="Summary 1", tokens_used=50),
            SummaryResult(success=True, content="Summary 2", tokens_used=75),
            SummaryResult(success=True, content="Summary 3", tokens_used=60)
        ]
        
        service = AIService("test-api-key")
        contents = ["Content 1", "Content 2", "Content 3"]
        results = service.batch_summarize(contents)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].content == "Summary 1"
        assert results[1].content == "Summary 2"
        assert results[2].content == "Summary 3"
        
        # Should have called summarize for each content
        assert mock_summarize.call_count == 3
        
        # Should have slept between requests (but not after the last one)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)
    
    @patch('services.ai_service.ClaudeAPIClient.summarize')
    def test_batch_summarize_empty_list(self, mock_summarize):
        """Test batch summarization with empty list"""
        service = AIService("test-api-key")
        results = service.batch_summarize([])
        
        assert results == []
        mock_summarize.assert_not_called()
    
    @patch('services.ai_service.ClaudeAPIClient.summarize')
    def test_batch_summarize_mixed_results(self, mock_summarize):
        """Test batch summarization with mixed success/failure results"""
        mock_summarize.side_effect = [
            SummaryResult(success=True, content="Summary 1", tokens_used=50),
            SummaryResult(success=False, error="API error"),
            SummaryResult(success=True, content="Summary 3", tokens_used=60)
        ]
        
        service = AIService("test-api-key")
        contents = ["Content 1", "Content 2", "Content 3"]
        results = service.batch_summarize(contents)
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert results[1].error == "API error"
    
    def test_combine_summaries_media_report(self):
        """Test combining summaries into media report"""
        service = AIService("test-api-key")
        summaries = ["Summary 1", "Summary 2", "Summary 3"]
        
        with patch('time.strftime', return_value='2024-01-15 10:30:00'):
            html_report = service.combine_summaries(summaries, "media")
        
        assert "<h1>Media Monitoring Report</h1>" in html_report
        assert "Generated on 2024-01-15 10:30:00" in html_report
        assert "political monitoring" in html_report
        assert "<h2>Summary 1</h2>" in html_report
        assert "<h2>Summary 2</h2>" in html_report
        assert "<h2>Summary 3</h2>" in html_report
        assert "<div>Summary 1</div>" in html_report
    
    def test_combine_summaries_hansard_report(self):
        """Test combining summaries into Hansard report"""
        service = AIService("test-api-key")
        summaries = ["Question 1", "Question 2"]
        
        html_report = service.combine_summaries(summaries, "hansard")
        
        assert "<h1>Hansard Questions Report</h1>" in html_report
        assert "parliamentary questions" in html_report
        assert "<h2>Summary 1</h2>" in html_report
        assert "<div>Question 1</div>" in html_report
    
    def test_combine_summaries_empty_list(self):
        """Test combining empty summaries list"""
        service = AIService("test-api-key")
        html_report = service.combine_summaries([])
        
        assert html_report == "<p>No summaries available.</p>"

class TestFactoryFunction:
    """Test cases for factory function"""
    
    def test_get_ai_service_default_url(self):
        """Test factory function with default URL"""
        service = get_ai_service("test-api-key")
        assert isinstance(service, AIService)
        assert service.client.api_key == "test-api-key"
        assert service.client.api_url == "https://api.anthropic.com/v1/messages"
    
    def test_get_ai_service_custom_url(self):
        """Test factory function with custom URL"""
        custom_url = "https://custom-api.example.com/v1/messages"
        service = get_ai_service("test-api-key", custom_url)
        assert isinstance(service, AIService)
        assert service.client.api_url == custom_url

class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @patch('requests.Session.post')
    def test_full_workflow_success(self, mock_post):
        """Test full workflow from service creation to summarization"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"text": "Comprehensive summary of the article content."}],
            "usage": {"output_tokens": 125}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create service and summarize content
        service = AIService("test-api-key")
        result = service.summarize_content("Long article content about politics and policy changes.")
        
        # Verify successful result
        assert result.success is True
        assert result.content == "Comprehensive summary of the article content."
        assert result.tokens_used == 125
        assert result.error is None
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "political monitoring report" in call_args[1]['json']['messages'][0]['content']
    
    @patch('requests.Session.post')
    def test_error_recovery_workflow(self, mock_post):
        """Test error recovery in workflow"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError("HTTP 500 Error", response=mock_response)
        mock_post.return_value = mock_response
        
        # Create service and attempt summarization
        service = AIService("test-api-key")
        result = service.summarize_content("Test content")
        
        # Should handle error gracefully
        assert result.success is False
        assert "HTTP error 500" in result.error
        assert result.content is None