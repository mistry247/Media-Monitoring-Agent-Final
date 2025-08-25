"""
Unit tests for the scraping service.

Tests cover normal operation, error scenarios, timeout handling,
and content validation with mock websites.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from services.scraping_service import ScrapingService, ScrapingError


class TestScrapingService:
    """Test cases for ScrapingService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScrapingService(timeout=5, max_retries=2, retry_delay=0.1)
    
    def test_init(self):
        """Test service initialization."""
        service = ScrapingService(timeout=10, max_retries=5, retry_delay=2.0)
        assert service.timeout == 10
        assert service.max_retries == 5
        assert service.retry_delay == 2.0
        assert service.session is not None
    
    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        valid_urls = [
            'https://example.com',
            'http://test.org/article',
            'https://news.site.com/path/to/article?param=value'
        ]
        
        for url in valid_urls:
            assert self.service._validate_url(url) is True
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',
            'javascript:alert(1)',
            '',
            'http://',
            'https://'
        ]
        
        for url in invalid_urls:
            assert self.service._validate_url(url) is False
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        # Test whitespace normalization
        text = "  This   has    excessive   whitespace  "
        cleaned = self.service._clean_text(text)
        assert cleaned == "This has excessive whitespace"
        
        # Test line break normalization
        text = "Line 1\n\n\n\nLine 2"
        cleaned = self.service._clean_text(text)
        assert cleaned == "Line 1\n\nLine 2"
        
        # Test empty text
        assert self.service._clean_text("") == ""
        assert self.service._clean_text(None) == ""
    
    @patch('services.scraping_service.Article')
    def test_extract_with_newspaper_success(self, mock_article_class):
        """Test successful content extraction with newspaper3k."""
        # Mock Article instance
        mock_article = Mock()
        mock_article.title = "Test Article Title"
        mock_article.text = "This is the article content with enough text to pass validation."
        mock_article.authors = ["John Doe", "Jane Smith"]
        mock_article.publish_date = "2024-01-15"
        mock_article_class.return_value = mock_article
        
        result = self.service._extract_with_newspaper("https://example.com")
        
        assert result is not None
        assert result['title'] == "Test Article Title"
        assert "article content" in result['text']
        assert result['authors'] == ["John Doe", "Jane Smith"]
        assert result['publish_date'] == "2024-01-15"
        
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()
    
    @patch('services.scraping_service.Article')
    def test_extract_with_newspaper_short_content(self, mock_article_class):
        """Test newspaper3k extraction with content too short."""
        mock_article = Mock()
        mock_article.title = "Short"
        mock_article.text = "Too short"  # Less than 50 characters
        mock_article_class.return_value = mock_article
        
        result = self.service._extract_with_newspaper("https://example.com")
        assert result is None
    
    @patch('services.scraping_service.Article')
    def test_extract_with_newspaper_exception(self, mock_article_class):
        """Test newspaper3k extraction with exception."""
        mock_article_class.side_effect = Exception("Download failed")
        
        result = self.service._extract_with_newspaper("https://example.com")
        assert result is None
    
    @patch('requests.Session.get')
    def test_extract_with_beautifulsoup_success(self, mock_get):
        """Test successful content extraction with BeautifulSoup."""
        # Mock HTML response
        html_content = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Article Headline</h1>
                    <p>This is the main content of the article with sufficient length for validation.</p>
                    <p>More content to ensure we pass the minimum length requirement.</p>
                </article>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service._extract_with_beautifulsoup("https://example.com")
        
        assert result is not None
        assert result['title'] == "Test Article"
        assert "main content" in result['text']
        assert result['authors'] == []
        assert result['publish_date'] is None
    
    @patch('requests.Session.get')
    def test_extract_with_beautifulsoup_http_error(self, mock_get):
        """Test BeautifulSoup extraction with HTTP error."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        result = self.service._extract_with_beautifulsoup("https://example.com")
        assert result is None
    
    @patch.object(ScrapingService, '_extract_with_newspaper')
    def test_scrape_article_success_newspaper(self, mock_newspaper):
        """Test successful article scraping with newspaper3k."""
        mock_newspaper.return_value = {
            'title': 'Test Title',
            'text': 'Test content',
            'authors': ['Author'],
            'publish_date': '2024-01-15'
        }
        
        result = self.service.scrape_article("https://example.com/article")
        
        assert result['success'] is True
        assert result['url'] == "https://example.com/article"
        assert result['title'] == 'Test Title'
        assert result['text'] == 'Test content'
        assert result['authors'] == ['Author']
        assert result['publish_date'] == '2024-01-15'
        assert result['error'] is None
    
    @patch.object(ScrapingService, '_extract_with_newspaper')
    @patch.object(ScrapingService, '_extract_with_beautifulsoup')
    def test_scrape_article_fallback_to_beautifulsoup(self, mock_bs, mock_newspaper):
        """Test fallback to BeautifulSoup when newspaper3k fails."""
        mock_newspaper.return_value = None
        mock_bs.return_value = {
            'title': 'BS Title',
            'text': 'BS content',
            'authors': [],
            'publish_date': None
        }
        
        result = self.service.scrape_article("https://example.com/article")
        
        assert result['success'] is True
        assert result['title'] == 'BS Title'
        assert result['text'] == 'BS content'
        mock_newspaper.assert_called_once()
        mock_bs.assert_called_once()
    
    def test_scrape_article_invalid_url(self):
        """Test scraping with invalid URL."""
        result = self.service.scrape_article("invalid-url")
        
        assert result['success'] is False
        assert result['error'] == 'Invalid URL format'
        assert result['url'] == "invalid-url"
    
    @patch.object(ScrapingService, '_extract_with_newspaper')
    @patch.object(ScrapingService, '_extract_with_beautifulsoup')
    def test_scrape_article_no_content_extracted(self, mock_bs, mock_newspaper):
        """Test scraping when no content can be extracted."""
        mock_newspaper.return_value = None
        mock_bs.return_value = None
        
        result = self.service.scrape_article("https://example.com/article")
        
        assert result['success'] is False
        assert result['error'] == "No content could be extracted"
    
    @patch.object(ScrapingService, '_extract_with_newspaper')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_scrape_article_timeout_with_retry(self, mock_sleep, mock_newspaper):
        """Test scraping with timeout and retry logic."""
        mock_newspaper.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.Timeout("Timeout"),
            {
                'title': 'Success after retries',
                'text': 'Content',
                'authors': [],
                'publish_date': None
            }
        ]
        
        # Set max_retries to 3 for this test
        self.service.max_retries = 3
        result = self.service.scrape_article("https://example.com/article")
        
        assert result['success'] is True
        assert result['title'] == 'Success after retries'
        assert mock_newspaper.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep called between retries
    
    @patch.object(ScrapingService, '_extract_with_newspaper')
    @patch('time.sleep')
    def test_scrape_article_max_retries_exceeded(self, mock_sleep, mock_newspaper):
        """Test scraping when max retries are exceeded."""
        mock_newspaper.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = self.service.scrape_article("https://example.com/article")
        
        assert result['success'] is False
        assert "Request timeout" in result['error']
        assert mock_newspaper.call_count == self.service.max_retries
    
    @patch.object(ScrapingService, '_extract_with_newspaper')
    def test_scrape_article_http_4xx_no_retry(self, mock_newspaper):
        """Test that 4xx HTTP errors don't trigger retries."""
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = Mock()
        http_error.response.status_code = 404
        mock_newspaper.side_effect = http_error
        
        result = self.service.scrape_article("https://example.com/article")
        
        assert result['success'] is False
        assert "HTTP error: 404" in result['error']
        assert mock_newspaper.call_count == 1  # No retries for 4xx
    
    @patch.object(ScrapingService, 'scrape_article')
    @patch('time.sleep')
    def test_batch_scrape_success(self, mock_sleep, mock_scrape):
        """Test successful batch scraping."""
        urls = [
            "https://example.com/article1",
            "https://example.com/article2",
            "https://example.com/article3"
        ]
        
        mock_scrape.side_effect = [
            {'success': True, 'url': urls[0], 'title': 'Article 1'},
            {'success': True, 'url': urls[1], 'title': 'Article 2'},
            {'success': False, 'url': urls[2], 'error': 'Failed'}
        ]
        
        results = self.service.batch_scrape(urls)
        
        assert len(results) == 3
        assert results[0]['success'] is True
        assert results[1]['success'] is True
        assert results[2]['success'] is False
        assert mock_scrape.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between requests
    
    def test_batch_scrape_empty_list(self):
        """Test batch scraping with empty URL list."""
        results = self.service.batch_scrape([])
        assert results == []
    
    @patch.object(ScrapingService, 'scrape_article')
    def test_batch_scrape_single_url(self, mock_scrape):
        """Test batch scraping with single URL."""
        mock_scrape.return_value = {'success': True, 'url': 'https://example.com'}
        
        results = self.service.batch_scrape(["https://example.com"])
        
        assert len(results) == 1
        assert results[0]['success'] is True
        mock_scrape.assert_called_once_with("https://example.com")


class TestScrapingServiceIntegration:
    """Integration tests for ScrapingService with real-like scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScrapingService(timeout=1, max_retries=1, retry_delay=0.1)
    
    @patch('requests.Session.get')
    @patch('services.scraping_service.Article')
    def test_full_scraping_workflow(self, mock_article_class, mock_get):
        """Test complete scraping workflow from URL to extracted content."""
        # Mock newspaper3k failure
        mock_article_class.side_effect = Exception("Newspaper failed")
        
        # Mock BeautifulSoup success
        html_content = """
        <html>
            <head><title>Integration Test Article</title></head>
            <body>
                <main>
                    <h1>Main Headline</h1>
                    <p>This is a comprehensive integration test for the scraping service.</p>
                    <p>It tests the complete workflow from URL validation to content extraction.</p>
                </main>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.scrape_article("https://integration-test.com/article")
        
        assert result['success'] is True
        assert result['title'] == "Integration Test Article"
        assert "comprehensive integration test" in result['text']
        assert result['url'] == "https://integration-test.com/article"