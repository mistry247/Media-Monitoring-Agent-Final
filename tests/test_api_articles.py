"""
Tests for article submission API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from main import app
from database import Base, get_db, PendingArticle, ProcessedArchive
from models.article import ArticleSubmission

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_articles_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """Set up test database for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_article_data():
    """Sample article submission data"""
    return {
        "url": "https://example.com/test-article",
        "submitted_by": "Test User"
    }

@pytest.fixture
def db_session():
    """Get database session for direct database operations"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestArticleSubmissionAPI:
    """Test cases for article submission API endpoints"""
    
    def test_submit_article_success(self, setup_database, sample_article_data):
        """Test successful article submission"""
        response = client.post("/api/articles/submit", json=sample_article_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert "successfully" in data["message"].lower()
        assert data["article"] is not None
        assert data["article"]["url"] == sample_article_data["url"]
        assert data["article"]["submitted_by"] == sample_article_data["submitted_by"]
        assert data["article"]["id"] is not None
        assert data["article"]["timestamp"] is not None
    
    def test_submit_article_invalid_url(self, setup_database):
        """Test article submission with invalid URL"""
        invalid_data = {
            "url": "not-a-valid-url",
            "submitted_by": "Test User"
        }
        
        response = client.post("/api/articles/submit", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_submit_article_empty_submitted_by(self, setup_database):
        """Test article submission with empty submitted_by field"""
        invalid_data = {
            "url": "https://example.com/test-article",
            "submitted_by": ""
        }
        
        response = client.post("/api/articles/submit", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_submit_article_missing_fields(self, setup_database):
        """Test article submission with missing required fields"""
        # Missing submitted_by
        response = client.post("/api/articles/submit", json={"url": "https://example.com/test"})
        assert response.status_code == 422
        
        # Missing url
        response = client.post("/api/articles/submit", json={"submitted_by": "Test User"})
        assert response.status_code == 422
        
        # Empty request
        response = client.post("/api/articles/submit", json={})
        assert response.status_code == 422
    
    def test_submit_duplicate_article_pending(self, setup_database, sample_article_data, db_session):
        """Test submitting duplicate article that exists in pending table"""
        # First submission should succeed
        response1 = client.post("/api/articles/submit", json=sample_article_data)
        assert response1.status_code == 201
        
        # Second submission should fail with conflict
        response2 = client.post("/api/articles/submit", json=sample_article_data)
        assert response2.status_code == 409  # Conflict
        
        data = response2.json()
        assert "already" in data["detail"].lower()
        assert "pending" in data["detail"].lower()
    
    def test_submit_duplicate_article_processed(self, setup_database, sample_article_data, db_session):
        """Test submitting duplicate article that exists in processed archive"""
        # Add article directly to processed archive
        processed_article = ProcessedArchive(
            url=sample_article_data["url"],
            timestamp=datetime.utcnow(),
            submitted_by=sample_article_data["submitted_by"],
            processed_date=datetime.utcnow()
        )
        db_session.add(processed_article)
        db_session.commit()
        
        # Submission should fail with conflict
        response = client.post("/api/articles/submit", json=sample_article_data)
        assert response.status_code == 409  # Conflict
        
        data = response.json()
        assert "already" in data["detail"].lower()
        assert "processed" in data["detail"].lower()
    
    def test_get_pending_articles_empty(self, setup_database):
        """Test retrieving pending articles when none exist"""
        response = client.get("/api/articles/pending")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["articles"] == []
        assert data["count"] == 0
    
    def test_get_pending_articles_with_data(self, setup_database, db_session):
        """Test retrieving pending articles with existing data"""
        # Add test articles to database
        articles = [
            PendingArticle(
                url="https://example.com/article1",
                submitted_by="User 1",
                timestamp=datetime.utcnow()
            ),
            PendingArticle(
                url="https://example.com/article2",
                submitted_by="User 2",
                timestamp=datetime.utcnow()
            )
        ]
        
        for article in articles:
            db_session.add(article)
        db_session.commit()
        
        response = client.get("/api/articles/pending")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["articles"]) == 2
        assert data["count"] == 2
        
        # Check article data structure
        article = data["articles"][0]
        assert "id" in article
        assert "url" in article
        assert "submitted_by" in article
        assert "timestamp" in article
    
    def test_get_pending_article_by_id_success(self, setup_database, sample_article_data):
        """Test retrieving specific pending article by ID"""
        # Submit an article first
        submit_response = client.post("/api/articles/submit", json=sample_article_data)
        assert submit_response.status_code == 201
        
        article_id = submit_response.json()["article"]["id"]
        
        # Retrieve the article by ID
        response = client.get(f"/api/articles/pending/{article_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == article_id
        assert data["url"] == sample_article_data["url"]
        assert data["submitted_by"] == sample_article_data["submitted_by"]
    
    def test_get_pending_article_by_id_not_found(self, setup_database):
        """Test retrieving non-existent article by ID"""
        response = client.get("/api/articles/pending/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_check_duplicate_url_not_duplicate(self, setup_database):
        """Test checking URL that is not a duplicate"""
        test_url = "https://example.com/unique-article"
        
        response = client.post("/api/articles/check-duplicate", json={"url": test_url})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["url"] == test_url
        assert data["is_duplicate"] is False
        assert data["location"] == "none"
    
    def test_check_duplicate_url_pending(self, setup_database, sample_article_data):
        """Test checking URL that exists in pending table"""
        # Submit an article first
        client.post("/api/articles/submit", json=sample_article_data)
        
        response = client.post("/api/articles/check-duplicate", json={"url": sample_article_data['url']})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["url"] == sample_article_data["url"]
        assert data["is_duplicate"] is True
        assert data["location"] == "pending"
    
    def test_check_duplicate_url_processed(self, setup_database, sample_article_data, db_session):
        """Test checking URL that exists in processed archive"""
        # Add article directly to processed archive
        processed_article = ProcessedArchive(
            url=sample_article_data["url"],
            timestamp=datetime.utcnow(),
            submitted_by=sample_article_data["submitted_by"],
            processed_date=datetime.utcnow()
        )
        db_session.add(processed_article)
        db_session.commit()
        
        response = client.post("/api/articles/check-duplicate", json={"url": sample_article_data['url']})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["url"] == sample_article_data["url"]
        assert data["is_duplicate"] is True
        assert data["location"] == "processed"
    
    def test_api_error_handling(self, setup_database):
        """Test API error handling for various scenarios"""
        # Test malformed JSON
        response = client.post(
            "/api/articles/submit",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test wrong content type
        response = client.post(
            "/api/articles/submit",
            data="url=test&submitted_by=user",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422
    
    def test_url_encoding_in_duplicate_check(self, setup_database):
        """Test URL encoding handling in duplicate check endpoint"""
        # Test URL with special characters
        encoded_url = "https://example.com/article?param=value&other=test"
        
        response = client.post("/api/articles/check-duplicate", json={"url": encoded_url})
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == encoded_url
    
    def test_check_duplicate_url_missing_url(self, setup_database):
        """Test duplicate check with missing URL"""
        response = client.post("/api/articles/check-duplicate", json={})
        
        assert response.status_code == 400
        data = response.json()
        assert "required" in data["detail"].lower()
    
    def test_get_pending_articles_database_error(self, setup_database, monkeypatch):
        """Test pending articles endpoint with database connection error"""
        from services.article_service import ArticleService
        
        def mock_get_pending_articles(self):
            """Mock method that raises database error"""
            raise Exception("Database connection failed")
        
        # Patch the get_pending_articles method to simulate database error
        monkeypatch.setattr(ArticleService, "get_pending_articles", mock_get_pending_articles)
        
        response = client.get("/api/articles/pending")
        
        assert response.status_code == 500
        data = response.json()
        assert "error occurred" in data["detail"].lower()
        assert "retrieving pending articles" in data["detail"].lower()

class TestArticleAPIIntegration:
    """Integration tests for article API workflows"""
    
    def test_complete_article_workflow(self, setup_database):
        """Test complete workflow: submit -> check pending -> retrieve by ID"""
        article_data = {
            "url": "https://example.com/workflow-test",
            "submitted_by": "Integration Test User"
        }
        
        # Step 1: Submit article
        submit_response = client.post("/api/articles/submit", json=article_data)
        assert submit_response.status_code == 201
        
        article_id = submit_response.json()["article"]["id"]
        
        # Step 2: Check it appears in pending list
        pending_response = client.get("/api/articles/pending")
        assert pending_response.status_code == 200
        
        pending_data = pending_response.json()
        assert pending_data["count"] == 1
        assert any(article["id"] == article_id for article in pending_data["articles"])
        
        # Step 3: Retrieve by ID
        get_response = client.get(f"/api/articles/pending/{article_id}")
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        assert get_data["url"] == article_data["url"]
        assert get_data["submitted_by"] == article_data["submitted_by"]
        
        # Step 4: Verify duplicate check
        duplicate_response = client.post("/api/articles/check-duplicate", json={"url": article_data['url']})
        assert duplicate_response.status_code == 200
        
        duplicate_data = duplicate_response.json()
        assert duplicate_data["is_duplicate"] is True
        assert duplicate_data["location"] == "pending"
    
    def test_multiple_articles_ordering(self, setup_database):
        """Test that multiple articles are returned in correct order (newest first)"""
        articles = [
            {"url": "https://example.com/article1", "submitted_by": "User 1"},
            {"url": "https://example.com/article2", "submitted_by": "User 2"},
            {"url": "https://example.com/article3", "submitted_by": "User 3"}
        ]
        
        submitted_ids = []
        
        # Submit articles with small delays to ensure different timestamps
        for article in articles:
            response = client.post("/api/articles/submit", json=article)
            assert response.status_code == 201
            submitted_ids.append(response.json()["article"]["id"])
        
        # Get pending articles
        response = client.get("/api/articles/pending")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] == 3
        
        # Verify ordering (newest first, so reverse order of submission)
        returned_ids = [article["id"] for article in data["articles"]]
        assert returned_ids == list(reversed(submitted_ids))