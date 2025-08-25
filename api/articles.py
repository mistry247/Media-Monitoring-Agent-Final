"""
API endpoints for article submission and management
"""
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.article import ArticleSubmission, Article, ArticleResponse, PendingArticlesResponse
from services.article_service import ArticleService
from utils.logging_config import get_logger, log_operation, log_error
from utils.error_handlers import (
    handle_database_error,
    handle_service_error,
    handle_generic_error,
    safe_execute,
    create_error_response,
    ArticleServiceError
)
from utils.security import InvalidInputError

logger = get_logger(__name__)

# Temporary minimal imports for testing - now using full import above

# Create router for article endpoints
router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("/submit")
async def submit_article(
    submission: ArticleSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit a new article URL for processing - MINIMAL DATABASE ONLY
    Only saves URL and submitter to database, no validation, no external operations
    """
    start_time = time.time()
    
    try:
        # Create new pending article directly - no validation, no duplicate checks, no external calls
        from database import PendingArticle
        from datetime import datetime
        
        new_article = PendingArticle(
            url=submission.url,
            submitted_by=submission.submitted_by,
            timestamp=datetime.utcnow()
        )
        
        db.add(new_article)
        db.commit()
        db.refresh(new_article)
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Article submitted successfully in {duration_ms:.2f}ms", extra={
            "article_id": new_article.id,
            "url": submission.url,
            "submitter": submission.submitted_by,
            "duration_ms": duration_ms
        })
        
        return {
            "success": True,
            "message": "Article submitted successfully",
            "id": new_article.id,
            "url": new_article.url,
            "submitted_by": new_article.submitted_by,
            "timestamp": new_article.timestamp.isoformat(),
            "status": "pending"
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        
        logger.error(f"Article submission failed: {e}", extra={
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/process/{article_id}")
async def process_article(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process a pending article: scrape content and generate AI summary
    
    Args:
        article_id: ID of the article to process
        request: FastAPI request object for tracking
        db: Database session dependency
        
    Returns:
        Dictionary with processing results and summary
    """
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', None)
    
    try:
        # Get the pending article
        from database import PendingArticle
        article = db.query(PendingArticle).filter(PendingArticle.id == article_id).first()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found"
            )
        
        logger.info(f"Processing article {article_id}: {article.url}")
        
        # Step 1: Scrape the article content
        print(f"🔍 Attempting to scrape URL: {article.url}")
        logger.info(f"Attempting to scrape URL: {article.url}")
        
        from services.scraping_service import ScrapingService
        scraping_service = ScrapingService()
        
        scrape_success, scraped_content, scrape_error = scraping_service.scrape_article_tuple(article.url)
        
        print(f"✅ Scraping completed. Success: {scrape_success}")
        logger.info(f"Scraping completed. Success: {scrape_success}")
        
        if not scrape_success:
            return {
                "success": False,
                "error": f"Failed to scrape article: {scrape_error}",
                "article_id": article_id,
                "url": article.url
            }
        
        # Step 2: Generate AI summary
        print(f"🤖 Attempting to call AI API for summarization...")
        logger.info(f"Attempting to call AI API for summarization...")
        
        from services.ai_service import AIService
        from config import settings
        
        ai_service = AIService(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL
        )
        
        summary_success, summary, ai_error = ai_service.summarize_article(
            scraped_content.get('title', ''),
            scraped_content.get('text', ''),  # Use 'text' instead of 'content'
            article.url
        )
        
        print(f"✅ AI summarization completed. Success: {summary_success}")
        logger.info(f"AI summarization completed. Success: {summary_success}")
        
        if not summary_success:
            return {
                "success": False,
                "error": f"Failed to generate summary: {ai_error}",
                "article_id": article_id,
                "url": article.url,
                "scraped_content": scraped_content
            }
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Article {article_id} processed successfully in {duration_ms:.2f}ms")
        
        return {
            "success": True,
            "message": "Article processed successfully",
            "article_id": article_id,
            "url": article.url,
            "submitted_by": article.submitted_by,
            "scraped_content": {
                "title": scraped_content.get('title', ''),
                "content": scraped_content.get('content', '')[:500] + "..." if len(scraped_content.get('content', '')) > 500 else scraped_content.get('content', ''),
                "author": scraped_content.get('author', ''),
                "publish_date": scraped_content.get('publish_date', ''),
                "word_count": len(scraped_content.get('content', '').split())
            },
            "ai_summary": summary,
            "processing_time_ms": duration_ms
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing article {article_id}: {e}")
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "article_id": article_id,
            "traceback": traceback.format_exc()
        }