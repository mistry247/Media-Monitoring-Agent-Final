"""
Integration tests for report generation service
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, PendingArticle, ProcessedArchive, HansardQuestion
from services.report_service import ReportService, ReportGenerationError
from services.ai_service import SummaryResult
from schemas import Article

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def test_db():
    """Create test database session"""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def sample_pending_articles(test_db):
    """Create sample pending articles for testing"""
    articles = [
        PendingArticle(
            url="https://example.com/article1",
            submitted_by="John Doe",
            timestamp=datetime.now()
        ),
        PendingArticle(
            url="https://example.com/article2",
            submitted_by="Jane Smith",
            timestamp=datetime.now()
        ),
        PendingArticle(
            url="https://example.com/article3",
            submitted_by="Bob Wilson",
            timestamp=datetime.now()
        )
    ]
    
    for article in articles:
        test_db.add(article)
    test_db.commit()
    
    return articles

@pytest.fixture
def mock_scraping_results():
    """Mock scraping service results"""
    return [
        {
            'success': True,
            'url': 'https://example.com/article1',
            'title': 'Test Article 1',
            'text': 'This is the content of test article 1 with political news.',
            'authors': ['Author 1'],
            'publish_date': '2024-01-01'
        },
        {
            'success': True,
            'url': 'https://example.com/article2',
            'title': 'Test Article 2',
            'text': 'This is the content of test article 2 with policy updates.',
            'authors': ['Author 2'],
            'publish_date': '2024-01-02'
        },
        {
            'success': False,
            'url': 'https://example.com/article3',
            'title': '',
            'text': '',
            'error': 'Connection timeout'
        }
    ]

@pytest.fixture
def mock_ai_results():
    """Mock AI service results"""
    return [
        SummaryResult(
            success=True,
            content="Summary of test article 1: Political developments and policy implications.",
            tokens_used=150
        ),
        SummaryResult(
            success=True,
            content="Summary of test article 2: Policy updates and government announcements.",
            tokens_used=120
        )
    ]

@pytest.fixture
def mock_hansard_result():
    """Mock Hansard AI result"""
    return SummaryResult(
        success=True,
        content="""1. To ask the Minister about the recent policy developments mentioned in media reports.
        
2. To ask the Government what steps are being taken regarding the issues raised in recent news coverage.
        
3. To ask the Prime Minister about the timeline for implementing the measures discussed in current media.""",
        tokens_used=200
    )

class TestReportService:
    """Test cases for ReportService"""
    
    @patch('services.report_service.settings')
    def test_init_without_api_key(self, mock_settings, test_db):
        """Test ReportService initialization without API key"""
        mock_settings.GEMINI_API_KEY = ""
        
        with pytest.raises(ValueError, match="Gemini API key is required"):
            ReportService(test_db)
    
    @patch('services.report_service.settings')
    def test_init_with_api_key(self, mock_settings, test_db):
        """Test ReportService initialization with API key"""
        mock_settings.GEMINI_API_KEY = "test-api-key"
        mock_settings.GEMINI_MODEL = "gemini-1.5-flash"
        
        service = ReportService(test_db)
        assert service.db == test_db
        assert service.article_service is not None
        assert service.ai_service is not None
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    @patch('services.report_service.email_service')
    def test_generate_media_report_success(self, mock_email, mock_scraping, mock_settings, 
                                         test_db, sample_pending_articles, mock_scraping_results, mock_ai_results):
        """Test successful media report generation"""
        # Setup mocks
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        mock_settings.CLAUDE_API_URL = "https://api.test.com"
        
        mock_scraping.scrape_article.side_effect = mock_scraping_results
        mock_email.format_html_report.return_value = "<html>Test Report</html>"
        mock_email.send_report.return_value = True
        
        # Create service with mocked AI service
        service = ReportService(test_db)
        service.ai_service = Mock()
        service.ai_service.batch_summarize.return_value = mock_ai_results
        
        # Test report generation
        success, message, report_id = service.generate_media_report("Additional pasted content")
        
        assert success is True
        assert "successfully" in message.lower()
        assert report_id is not None
        assert report_id.startswith("media_report_")
        
        # Verify scraping was called for each article
        assert mock_scraping.scrape_article.call_count == 3
        
        # Verify AI service was called
        service.ai_service.batch_summarize.assert_called_once()
        
        # Verify email was sent
        mock_email.send_report.assert_called_once()
        
        # Verify articles were archived (only successful ones)
        archived_articles = test_db.query(ProcessedArchive).all()
        assert len(archived_articles) == 2  # Only successful scrapes
    
    @patch('services.report_service.settings')
    def test_generate_media_report_no_content(self, mock_settings, test_db):
        """Test media report generation with no content"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        service = ReportService(test_db)
        
        success, message, report_id = service.generate_media_report("")
        
        assert success is False
        assert "no pending articles" in message.lower()
        assert report_id is None
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    def test_generate_media_report_scraping_failures(self, mock_scraping, mock_settings, 
                                                   test_db, sample_pending_articles):
        """Test media report generation with all scraping failures"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        # Mock all scraping attempts to fail
        mock_scraping.scrape_article.return_value = {
            'success': False,
            'error': 'Connection failed'
        }
        
        service = ReportService(test_db)
        
        success, message, report_id = service.generate_media_report("")
        
        assert success is False
        assert "no content available" in message.lower()
        assert report_id is None
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    @patch('services.report_service.email_service')
    def test_generate_media_report_ai_failures(self, mock_email, mock_scraping, mock_settings,
                                             test_db, sample_pending_articles, mock_scraping_results):
        """Test media report generation with AI summarization failures"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        mock_scraping.scrape_article.side_effect = mock_scraping_results
        
        service = ReportService(test_db)
        service.ai_service = Mock()
        
        # Mock AI service to return all failures
        service.ai_service.batch_summarize.return_value = [
            SummaryResult(success=False, error="API rate limit exceeded"),
            SummaryResult(success=False, error="Content too long")
        ]
        
        success, message, report_id = service.generate_media_report("")
        
        assert success is False
        assert "summarization attempts failed" in message.lower()
        assert report_id is None
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    @patch('services.report_service.email_service')
    def test_generate_media_report_email_failure(self, mock_email, mock_scraping, mock_settings,
                                               test_db, sample_pending_articles, mock_scraping_results, mock_ai_results):
        """Test media report generation with email sending failure"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        mock_scraping.scrape_article.side_effect = mock_scraping_results
        mock_email.format_html_report.return_value = "<html>Test Report</html>"
        mock_email.send_report.return_value = False  # Email fails
        
        service = ReportService(test_db)
        service.ai_service = Mock()
        service.ai_service.batch_summarize.return_value = mock_ai_results
        
        success, message, report_id = service.generate_media_report("")
        
        assert success is False
        assert "email sending failed" in message.lower()
        assert report_id is not None  # Report was generated, just email failed
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    @patch('services.report_service.email_service')
    def test_generate_hansard_report_success(self, mock_email, mock_scraping, mock_settings,
                                           test_db, sample_pending_articles, mock_scraping_results, mock_hansard_result):
        """Test successful Hansard report generation"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        mock_scraping.scrape_article.side_effect = mock_scraping_results
        mock_email.format_html_report.return_value = "<html>Hansard Report</html>"
        mock_email.send_report.return_value = True
        
        service = ReportService(test_db)
        service.ai_service = Mock()
        service.ai_service.summarize_content.return_value = mock_hansard_result
        
        success, message, report_id = service.generate_hansard_report()
        
        assert success is True
        assert "successfully" in message.lower()
        assert report_id is not None
        assert report_id.startswith("hansard_report_")
        
        # Verify Hansard question was saved to database
        hansard_questions = test_db.query(HansardQuestion).all()
        assert len(hansard_questions) == 1
        assert hansard_questions[0].question_text == mock_hansard_result.content
        assert hansard_questions[0].category == "Media-based Questions"
        
        # Verify email was sent
        mock_email.send_report.assert_called_once()
    
    @patch('services.report_service.settings')
    def test_generate_hansard_report_no_articles(self, mock_settings, test_db):
        """Test Hansard report generation with no pending articles"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        service = ReportService(test_db)
        
        success, message, report_id = service.generate_hansard_report()
        
        assert success is False
        assert "no pending articles" in message.lower()
        assert report_id is None
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    def test_generate_hansard_report_ai_failure(self, mock_scraping, mock_settings,
                                              test_db, sample_pending_articles, mock_scraping_results):
        """Test Hansard report generation with AI failure"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        mock_scraping.scrape_article.side_effect = mock_scraping_results
        
        service = ReportService(test_db)
        service.ai_service = Mock()
        service.ai_service.summarize_content.return_value = SummaryResult(
            success=False, 
            error="API authentication failed"
        )
        
        success, message, report_id = service.generate_hansard_report()
        
        assert success is False
        assert "failed to generate hansard questions" in message.lower()
        assert report_id is None
    
    @patch('services.report_service.settings')
    def test_get_recent_hansard_questions(self, mock_settings, test_db):
        """Test retrieving recent Hansard questions"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        # Create test Hansard questions
        questions = [
            HansardQuestion(
                question_text="Test question 1",
                category="Test Category",
                timestamp=datetime.now(),
                source_articles=json.dumps([1, 2])
            ),
            HansardQuestion(
                question_text="Test question 2",
                category="Test Category",
                timestamp=datetime.now(),
                source_articles=json.dumps([3, 4])
            )
        ]
        
        for question in questions:
            test_db.add(question)
        test_db.commit()
        
        service = ReportService(test_db)
        recent_questions = service.get_recent_hansard_questions(limit=5)
        
        assert len(recent_questions) == 2
        assert recent_questions[0]['question_text'] == "Test question 2"  # Most recent first
        assert recent_questions[1]['question_text'] == "Test question 1"
        assert recent_questions[0]['source_articles'] == [3, 4]
    
    @patch('services.report_service.settings')
    def test_get_report_status(self, mock_settings, test_db):
        """Test getting report status"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        service = ReportService(test_db)
        status = service.get_report_status("test_report_123")
        
        assert status['report_id'] == "test_report_123"
        assert status['status'] == "completed"
        assert "not yet implemented" in status['message']
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    @patch('services.report_service.email_service')
    def test_generate_media_report_with_rollback(self, mock_email, mock_scraping, mock_settings,
                                                test_db, sample_pending_articles, mock_scraping_results):
        """Test media report generation with database rollback on error"""
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        
        mock_scraping.scrape_article.side_effect = mock_scraping_results
        mock_email.format_html_report.return_value = "<html>Test Report</html>"
        mock_email.send_report.side_effect = Exception("Email server error")
        
        service = ReportService(test_db)
        service.ai_service = Mock()
        service.ai_service.batch_summarize.return_value = [
            SummaryResult(success=True, content="Test summary", tokens_used=100)
        ]
        
        success, message, report_id = service.generate_media_report("")
        
        assert success is False
        assert "failed" in message.lower()
        assert report_id is None
        
        # Verify no articles were archived due to rollback
        archived_articles = test_db.query(ProcessedArchive).all()
        assert len(archived_articles) == 0

class TestReportServiceIntegration:
    """Integration tests for complete workflows"""
    
    @patch('services.report_service.settings')
    @patch('services.report_service.scraping_service')
    @patch('services.report_service.email_service')
    def test_complete_media_workflow(self, mock_email, mock_scraping, mock_settings, test_db):
        """Test complete media report workflow from start to finish"""
        # Setup
        mock_settings.CLAUDE_API_KEY = "test-api-key"
        mock_settings.CLAUDE_API_URL = "https://api.test.com"
        
        # Create test data
        article = PendingArticle(
            url="https://example.com/test-article",
            submitted_by="Test User",
            timestamp=datetime.now()
        )
        test_db.add(article)
        test_db.commit()
        
        # Mock external services
        mock_scraping.scrape_article.return_value = {
            'success': True,
            'url': 'https://example.com/test-article',
            'title': 'Integration Test Article',
            'text': 'This is a comprehensive test of the media monitoring system.',
            'authors': ['Test Author'],
            'publish_date': '2024-01-01'
        }
        
        mock_email.format_html_report.return_value = "<html>Integration Test Report</html>"
        mock_email.send_report.return_value = True
        
        # Create service and mock AI
        service = ReportService(test_db)
        service.ai_service = Mock()
        service.ai_service.batch_summarize.return_value = [
            SummaryResult(
                success=True,
                content="Integration test summary of political developments.",
                tokens_used=150
            )
        ]
        
        # Execute workflow
        success, message, report_id = service.generate_media_report("Additional test content")
        
        # Verify results
        assert success is True
        assert report_id is not None
        
        # Verify database state
        pending_count = test_db.query(PendingArticle).count()
        archived_count = test_db.query(ProcessedArchive).count()
        
        assert pending_count == 0  # Article should be moved to archive
        assert archived_count == 1  # Article should be in archive
        
        # Verify archived article data
        archived_article = test_db.query(ProcessedArchive).first()
        assert archived_article.url == "https://example.com/test-article"
        assert archived_article.submitted_by == "Test User"
        assert archived_article.processed_date is not None