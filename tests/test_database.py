"""
Unit tests for database models and operations
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from database import Base, PendingArticle, ProcessedArchive, HansardQuestion

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

def test_pending_article_creation(test_db):
    """Test creating a pending article"""
    article = PendingArticle(
        url="https://example.com/article1",
        submitted_by="Test User",
        pasted_text="Some pasted content"
    )
    
    test_db.add(article)
    test_db.commit()
    
    # Verify article was created
    saved_article = test_db.query(PendingArticle).filter(
        PendingArticle.url == "https://example.com/article1"
    ).first()
    
    assert saved_article is not None
    assert saved_article.url == "https://example.com/article1"
    assert saved_article.submitted_by == "Test User"
    assert saved_article.pasted_text == "Some pasted content"
    assert saved_article.timestamp is not None
    assert isinstance(saved_article.timestamp, datetime)

def test_pending_article_unique_url_constraint(test_db):
    """Test that URL uniqueness constraint works"""
    # Create first article
    article1 = PendingArticle(
        url="https://example.com/duplicate",
        submitted_by="User 1"
    )
    test_db.add(article1)
    test_db.commit()
    
    # Try to create second article with same URL
    article2 = PendingArticle(
        url="https://example.com/duplicate",
        submitted_by="User 2"
    )
    test_db.add(article2)
    
    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        test_db.commit()

def test_processed_archive_creation(test_db):
    """Test creating a processed archive entry"""
    archive = ProcessedArchive(
        url="https://example.com/processed",
        timestamp=datetime.utcnow(),
        submitted_by="Test User"
    )
    
    test_db.add(archive)
    test_db.commit()
    
    # Verify archive was created
    saved_archive = test_db.query(ProcessedArchive).filter(
        ProcessedArchive.url == "https://example.com/processed"
    ).first()
    
    assert saved_archive is not None
    assert saved_archive.url == "https://example.com/processed"
    assert saved_archive.submitted_by == "Test User"
    assert saved_archive.processed_date is not None

def test_hansard_question_creation(test_db):
    """Test creating a Hansard question"""
    question = HansardQuestion(
        question_text="What is the government's position on climate change?",
        category="Environment",
        source_articles='["1", "2", "3"]'
    )
    
    test_db.add(question)
    test_db.commit()
    
    # Verify question was created
    saved_question = test_db.query(HansardQuestion).first()
    
    assert saved_question is not None
    assert saved_question.question_text == "What is the government's position on climate change?"
    assert saved_question.category == "Environment"
    assert saved_question.source_articles == '["1", "2", "3"]'
    assert saved_question.timestamp is not None

def test_pending_article_required_fields(test_db):
    """Test that required fields are enforced"""
    # Test missing URL
    with pytest.raises(Exception):
        article = PendingArticle(submitted_by="Test User")
        test_db.add(article)
        test_db.commit()
    
    test_db.rollback()
    
    # Test missing submitted_by
    with pytest.raises(Exception):
        article = PendingArticle(url="https://example.com/test")
        test_db.add(article)
        test_db.commit()

def test_multiple_articles_different_urls(test_db):
    """Test that multiple articles with different URLs can be created"""
    articles = [
        PendingArticle(url="https://example.com/article1", submitted_by="User 1"),
        PendingArticle(url="https://example.com/article2", submitted_by="User 2"),
        PendingArticle(url="https://example.com/article3", submitted_by="User 1"),
    ]
    
    for article in articles:
        test_db.add(article)
    
    test_db.commit()
    
    # Verify all articles were created
    saved_articles = test_db.query(PendingArticle).all()
    assert len(saved_articles) == 3
    
    urls = [article.url for article in saved_articles]
    assert "https://example.com/article1" in urls
    assert "https://example.com/article2" in urls
    assert "https://example.com/article3" in urls