"""
Unit tests for Article Service
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, PendingArticle, ProcessedArchive
from services.article_service import ArticleService
from schemas import ArticleSubmission

# Create test database engine (in-memory SQLite)
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
def article_service(test_db):
    """Create ArticleService instance with test database"""
    return ArticleService(test_db)

def test_submit_article_success(article_service):
    """Test successful article submission"""
    submission = ArticleSubmission(
        url="https://example.com/article1",
        submitted_by="Test User"
    )
    
    success, message, article = article_service.submit_article(submission)
    
    assert success is True
    assert "successfully" in message.lower()
    assert article is not None
    assert article.url == "https://example.com/article1"
    assert article.submitted_by == "Test User"
    assert article.id is not None

def test_submit_article_duplicate_pending(article_service):
    """Test submitting duplicate URL that exists in pending_articles"""
    # Submit first article
    submission1 = ArticleSubmission(
        url="https://example.com/duplicate",
        submitted_by="User 1"
    )
    article_service.submit_article(submission1)
    
    # Try to submit duplicate
    submission2 = ArticleSubmission(
        url="https://example.com/duplicate",
        submitted_by="User 2"
    )
    
    success, message, article = article_service.submit_article(submission2)
    
    assert success is False
    assert "already pending" in message.lower()
    assert article is None

def test_submit_article_duplicate_processed(article_service, test_db):
    """Test submitting duplicate URL that exists in processed_archive"""
    # Add article to processed archive
    processed_article = ProcessedArchive(
        url="https://example.com/processed",
        timestamp=datetime.utcnow(),
        submitted_by="Previous User",
        processed_date=datetime.utcnow()
    )
    test_db.add(processed_article)
    test_db.commit()
    
    # Try to submit same URL
    submission = ArticleSubmission(
        url="https://example.com/processed",
        submitted_by="New User"
    )
    
    success, message, article = article_service.submit_article(submission)
    
    assert success is False
    assert "already been processed" in message.lower()
    assert article is None

def test_get_pending_articles_empty(article_service):
    """Test retrieving pending articles when none exist"""
    articles = article_service.get_pending_articles()
    
    assert articles == []

def test_get_pending_articles_with_data(article_service):
    """Test retrieving pending articles with data"""
    # Submit multiple articles
    submissions = [
        ArticleSubmission(url="https://example.com/article1", submitted_by="User 1"),
        ArticleSubmission(url="https://example.com/article2", submitted_by="User 2"),
        ArticleSubmission(url="https://example.com/article3", submitted_by="User 1"),
    ]
    
    for submission in submissions:
        article_service.submit_article(submission)
    
    articles = article_service.get_pending_articles()
    
    assert len(articles) == 3
    # Should be ordered by timestamp desc (newest first)
    assert articles[0].url == "https://example.com/article3"  # Last submitted
    assert articles[2].url == "https://example.com/article1"  # First submitted

def test_get_pending_article_by_id(article_service):
    """Test retrieving specific pending article by ID"""
    submission = ArticleSubmission(
        url="https://example.com/specific",
        submitted_by="Test User"
    )
    
    success, message, submitted_article = article_service.submit_article(submission)
    assert success is True
    
    # Retrieve by ID
    retrieved_article = article_service.get_pending_article_by_id(submitted_article.id)
    
    assert retrieved_article is not None
    assert retrieved_article.id == submitted_article.id
    assert retrieved_article.url == submitted_article.url
    assert retrieved_article.submitted_by == submitted_article.submitted_by

def test_get_pending_article_by_id_not_found(article_service):
    """Test retrieving non-existent article by ID"""
    article = article_service.get_pending_article_by_id(999)
    assert article is None

def test_move_to_archive_success(article_service):
    """Test successfully moving articles to archive"""
    # Submit articles
    submissions = [
        ArticleSubmission(url="https://example.com/archive1", submitted_by="User 1"),
        ArticleSubmission(url="https://example.com/archive2", submitted_by="User 2"),
    ]
    
    article_ids = []
    for submission in submissions:
        success, message, article = article_service.submit_article(submission)
        article_ids.append(article.id)
    
    # Move to archive
    success, message, archived_count = article_service.move_to_archive(article_ids)
    
    assert success is True
    assert archived_count == 2
    assert "successfully archived 2" in message.lower()
    
    # Verify articles are no longer pending
    pending_articles = article_service.get_pending_articles()
    assert len(pending_articles) == 0
    
    # Verify articles are in archive
    processed_articles = article_service.get_processed_articles()
    assert len(processed_articles) == 2

def test_move_to_archive_nonexistent_id(article_service):
    """Test moving non-existent article to archive"""
    success, message, archived_count = article_service.move_to_archive([999])
    
    # Should still succeed but with 0 archived
    assert success is True
    assert archived_count == 0

def test_move_to_archive_mixed_ids(article_service):
    """Test moving mix of valid and invalid IDs to archive"""
    # Submit one article
    submission = ArticleSubmission(
        url="https://example.com/mixed",
        submitted_by="User 1"
    )
    success, message, article = article_service.submit_article(submission)
    valid_id = article.id
    
    # Try to archive valid and invalid IDs
    success, message, archived_count = article_service.move_to_archive([valid_id, 999])
    
    assert success is True
    assert archived_count == 1  # Only valid ID should be archived

def test_get_processed_articles(article_service):
    """Test retrieving processed articles"""
    # Submit and archive an article
    submission = ArticleSubmission(
        url="https://example.com/processed",
        submitted_by="Test User"
    )
    success, message, article = article_service.submit_article(submission)
    article_service.move_to_archive([article.id])
    
    # Retrieve processed articles
    processed_articles = article_service.get_processed_articles()
    
    assert len(processed_articles) == 1
    assert processed_articles[0]["url"] == "https://example.com/processed"
    assert processed_articles[0]["submitted_by"] == "Test User"
    assert "processed_date" in processed_articles[0]

def test_is_url_duplicate_none(article_service):
    """Test URL duplicate check when URL doesn't exist"""
    is_duplicate, location = article_service.is_url_duplicate("https://example.com/new")
    
    assert is_duplicate is False
    assert location == "none"

def test_is_url_duplicate_pending(article_service):
    """Test URL duplicate check when URL exists in pending"""
    submission = ArticleSubmission(
        url="https://example.com/pending",
        submitted_by="Test User"
    )
    article_service.submit_article(submission)
    
    is_duplicate, location = article_service.is_url_duplicate("https://example.com/pending")
    
    assert is_duplicate is True
    assert location == "pending"

def test_is_url_duplicate_processed(article_service, test_db):
    """Test URL duplicate check when URL exists in processed archive"""
    # Add directly to processed archive
    processed_article = ProcessedArchive(
        url="https://example.com/processed",
        timestamp=datetime.utcnow(),
        submitted_by="Test User",
        processed_date=datetime.utcnow()
    )
    test_db.add(processed_article)
    test_db.commit()
    
    is_duplicate, location = article_service.is_url_duplicate("https://example.com/processed")
    
    assert is_duplicate is True
    assert location == "processed"

def test_get_processed_articles_with_limit(article_service):
    """Test retrieving processed articles with limit"""
    # Submit and archive multiple articles
    for i in range(5):
        submission = ArticleSubmission(
            url=f"https://example.com/article{i}",
            submitted_by=f"User {i}"
        )
        success, message, article = article_service.submit_article(submission)
        article_service.move_to_archive([article.id])
    
    # Retrieve with limit
    processed_articles = article_service.get_processed_articles(limit=3)
    
    assert len(processed_articles) == 3