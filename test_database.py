#!/usr/bin/env python3
"""
Test database operations to see if they're causing the 500 error
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db, PendingArticle
from schemas import ArticleSubmission
from services.article_service import ArticleService

def test_database():
    print("Testing database operations...")
    
    try:
        # Get database session
        db = next(get_db())
        print("✅ Database connection successful")
        
        # Test ArticleService
        article_service = ArticleService(db)
        print("✅ ArticleService created")
        
        # Test submission
        submission = ArticleSubmission(
            url="https://example.com/test-database",
            submitted_by="Test User"
        )
        print("✅ ArticleSubmission created")
        
        # Try to submit
        success, message, article = article_service.submit_article(submission)
        print(f"✅ Article submission result: success={success}, message='{message}'")
        
        if article:
            print(f"   Article ID: {article.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database()