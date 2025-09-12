"""
API endpoints for manual article processing
"""
import time
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db, ManualInputArticle
from services.ai_service import get_ai_service
from services.email_service import EmailService
from services.article_service import ArticleService, update_manual_articles_content
from services.report_service import ReportService
from config import settings
from utils.logging_config import get_logger
from schemas import ManualArticleBatchPayload
from utils.error_handlers import create_error_response

logger = get_logger(__name__)

# Create router for manual articles endpoints
router = APIRouter(prefix="/api/manual-articles", tags=["manual-articles"])

# Pydantic models for request/response
class ManualArticleResponse(BaseModel):
    id: int
    url: str
    submitted_by: str
    submitted_at: str
    article_content: str = None
    has_content: bool

class UpdateContentRequest(BaseModel):
    article_content: str

class ProcessBatchRequest(BaseModel):
    recipient_email: str = None

@router.get("/", response_model=List[ManualArticleResponse])
async def get_manual_articles(db: Session = Depends(get_db)):
    """
    Get all articles waiting for manual input
    
    Returns:
        List of manual articles with their current content status
    """
    try:
        manual_articles = db.query(ManualInputArticle).order_by(
            ManualInputArticle.submitted_at.desc()
        ).all()
        
        articles_response = []
        for article in manual_articles:
            # Calculate has_content dynamically since the database column might not exist
            has_content = bool(article.article_content and article.article_content.strip())
            
            articles_response.append(ManualArticleResponse(
                id=article.id,
                url=article.url,
                submitted_by=article.submitted_by,
                submitted_at=article.submitted_at.isoformat(),
                article_content=article.article_content or "",
                has_content=has_content
            ))
        
        logger.info(f"Retrieved {len(articles_response)} manual articles")
        
        return articles_response
        
    except Exception as e:
        logger.error(f"Error retrieving manual articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve manual articles"
        )

@router.post("/process-batch", status_code=status.HTTP_202_ACCEPTED)
async def process_manual_articles_batch(
    payload: ManualArticleBatchPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Updates content for a batch of articles and triggers report generation.
    """
    updated_ids = await update_manual_articles_content(db, payload.articles)

    if not updated_ids:
        raise HTTPException(status_code=400, detail="No articles were found or updated.")

    job_id = f"manual_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Create ReportService instance and call the method
    report_service_instance = ReportService(db)
    background_tasks.add_task(
        report_service_instance.generate_manual_report,
        article_ids=updated_ids,
        recipient_email=payload.recipient_email,
        job_id=job_id,
        db=db
    )
    
    logger.info(f"Queued background task {job_id} to process {len(updated_ids)} manual articles.")
    return {"message": "Manual article processing has been started.", "job_id": job_id, "processed_ids": updated_ids}

@router.post("/{article_id}")
async def update_article_content(
    article_id: int,
    request: UpdateContentRequest,
    db: Session = Depends(get_db)
):
    """
    Save the pasted text content for a specific article
    
    Args:
        article_id: ID of the article to update
        request: Request containing the article content
        
    Returns:
        Success message with updated article info
    """
    try:
        # Find the article
        article = db.query(ManualInputArticle).filter(
            ManualInputArticle.id == article_id
        ).first()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manual article with ID {article_id} not found"
            )
        
        # Update the content
        article.article_content = request.article_content.strip()
        db.commit()
        db.refresh(article)
        
        logger.info(f"Updated content for manual article {article_id} ({article.url})")
        
        return {
            "success": True,
            "message": "Article content updated successfully",
            "id": article.id,
            "url": article.url,
            "content_length": len(article.article_content) if article.article_content else 0,
            "has_content": bool(article.article_content and article.article_content.strip())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating article content for {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update article content"
        )

@router.delete("/{article_id}")
async def remove_manual_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove an article from the manual queue
    
    Args:
        article_id: ID of the article to remove
        
    Returns:
        Success message
    """
    try:
        # Find the article
        article = db.query(ManualInputArticle).filter(
            ManualInputArticle.id == article_id
        ).first()
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manual article with ID {article_id} not found"
            )
        
        # Store info for logging before deletion
        article_url = article.url
        article_submitter = article.submitted_by
        
        # Delete the article
        db.delete(article)
        db.commit()
        
        logger.info(f"Removed manual article {article_id} ({article_url}) submitted by {article_submitter}")
        
        return {
            "success": True,
            "message": "Article removed from manual queue",
            "id": article_id,
            "url": article_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing manual article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove article"
        )