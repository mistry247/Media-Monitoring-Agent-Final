"""
Unit tests for Pydantic models and validation
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from models.article import ArticleSubmission, Article, ArticleResponse, PendingArticlesResponse
from models.report import MediaReportRequest, HansardReportRequest, ReportResponse, ReportStatus

def test_article_submission_valid():
    """Test valid article submission"""
    submission = ArticleSubmission(
        url="https://example.com/article",
        submitted_by="Test User"
    )
    
    assert submission.url == "https://example.com/article"
    assert submission.submitted_by == "Test User"

def test_article_submission_invalid_url():
    """Test article submission with invalid URL"""
    with pytest.raises(ValidationError) as exc_info:
        ArticleSubmission(
            url="not-a-valid-url",
            submitted_by="Test User"
        )
    
    assert "url" in str(exc_info.value)

def test_article_submission_empty_submitted_by():
    """Test article submission with empty submitted_by"""
    with pytest.raises(ValidationError) as exc_info:
        ArticleSubmission(
            url="https://example.com/article",
            submitted_by=""
        )
    
    assert "submitted_by cannot be empty" in str(exc_info.value)

def test_article_submission_whitespace_submitted_by():
    """Test article submission with whitespace-only submitted_by"""
    with pytest.raises(ValidationError) as exc_info:
        ArticleSubmission(
            url="https://example.com/article",
            submitted_by="   "
        )
    
    assert "submitted_by cannot be empty" in str(exc_info.value)

def test_article_submission_strips_whitespace():
    """Test that submitted_by whitespace is stripped"""
    submission = ArticleSubmission(
        url="https://example.com/article",
        submitted_by="  Test User  "
    )
    
    assert submission.submitted_by == "Test User"

def test_article_model():
    """Test Article model"""
    article = Article(
        id=1,
        url="https://example.com/article",
        pasted_text="Some content",
        timestamp=datetime.utcnow(),
        submitted_by="Test User"
    )
    
    assert article.id == 1
    assert article.url == "https://example.com/article"
    assert article.pasted_text == "Some content"
    assert article.submitted_by == "Test User"
    assert isinstance(article.timestamp, datetime)

def test_article_response():
    """Test ArticleResponse model"""
    response = ArticleResponse(
        success=True,
        message="Article submitted successfully"
    )
    
    assert response.success is True
    assert response.message == "Article submitted successfully"
    assert response.article is None

def test_pending_articles_response():
    """Test PendingArticlesResponse model"""
    articles = [
        Article(
            id=1,
            url="https://example.com/article1",
            timestamp=datetime.utcnow(),
            submitted_by="User 1"
        ),
        Article(
            id=2,
            url="https://example.com/article2",
            timestamp=datetime.utcnow(),
            submitted_by="User 2"
        )
    ]
    
    response = PendingArticlesResponse(
        articles=articles,
        count=2
    )
    
    assert len(response.articles) == 2
    assert response.count == 2

def test_media_report_request_valid():
    """Test valid media report request"""
    request = MediaReportRequest(
        pasted_content="Some article content to process"
    )
    
    assert request.pasted_content == "Some article content to process"

def test_media_report_request_empty_content():
    """Test media report request with empty content"""
    request = MediaReportRequest(pasted_content="")
    assert request.pasted_content == ""

def test_media_report_request_strips_whitespace():
    """Test that pasted_content whitespace is stripped"""
    request = MediaReportRequest(
        pasted_content="  Some content  "
    )
    
    assert request.pasted_content == "Some content"

def test_media_report_request_too_long():
    """Test media report request with content too long"""
    long_content = "x" * 100001  # Exceeds 100KB limit
    
    with pytest.raises(ValidationError) as exc_info:
        MediaReportRequest(pasted_content=long_content)
    
    assert "exceeds maximum length" in str(exc_info.value)

def test_hansard_report_request():
    """Test HansardReportRequest model"""
    request = HansardReportRequest()
    # Should create successfully with no fields
    assert request is not None

def test_report_response():
    """Test ReportResponse model"""
    response = ReportResponse(
        success=True,
        message="Report generated successfully",
        report_id="report_123"
    )
    
    assert response.success is True
    assert response.message == "Report generated successfully"
    assert response.report_id == "report_123"

def test_report_status():
    """Test ReportStatus model"""
    status = ReportStatus(
        report_id="report_123",
        status="processing",
        message="Generating report...",
        progress=50
    )
    
    assert status.report_id == "report_123"
    assert status.status == "processing"
    assert status.message == "Generating report..."
    assert status.progress == 50