from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

from utils.security import validate_and_sanitize_url, validate_and_sanitize_name, validate_and_sanitize_text

class ArticleSubmission(BaseModel):
    """Model for article submission requests"""
    url: str
    submitted_by: str
    
    @validator('submitted_by')
    def validate_submitted_by(cls, v):
        # Use security utility for name validation
        return validate_and_sanitize_name(v, max_length=100)
    
    @validator('url')
    def validate_url(cls, v):
        # Use security utility for URL validation and sanitization
        return validate_and_sanitize_url(str(v))

class Article(BaseModel):
    """Model for article data"""
    id: Optional[int] = None
    url: str
    pasted_text: Optional[str] = None
    timestamp: datetime
    submitted_by: str
    
    class Config:
        from_attributes = True

class ArticleResponse(BaseModel):
    """Model for article API responses"""
    success: bool
    message: str
    article: Optional[Article] = None

class PendingArticlesResponse(BaseModel):
    """Model for pending articles list response"""
    articles: List[Article]
    count: int

class ManualArticleUpdate(BaseModel):
    id: int
    content: str

class ManualArticleBatchPayload(BaseModel):
    articles: List[ManualArticleUpdate]
    recipient_email: str

class MediaReportRequest(BaseModel):
    """Model for media report generation requests"""
    pasted_content: str
    recipient_email: str
    
    @validator('pasted_content')
    def validate_pasted_content(cls, v):
        # Use security utility for text validation and sanitization
        return validate_and_sanitize_text(v, max_length=100000)
    
    @validator('recipient_email')
    def validate_recipient_email(cls, v):
        # Basic email validation
        import re
        if not v or not v.strip():
            raise ValueError('Recipient email is required')
        
        email = v.strip()
        if len(email) > 254:
            raise ValueError('Email address is too long')
        
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise ValueError('Invalid email address format')
        
        return email

class HansardReportRequest(BaseModel):
    """Model for Hansard report generation requests"""
    recipient_email: str
    
    @validator('recipient_email')
    def validate_recipient_email(cls, v):
        # Basic email validation
        import re
        if not v or not v.strip():
            raise ValueError('Recipient email is required')
        
        email = v.strip()
        if len(email) > 254:
            raise ValueError('Email address is too long')
        
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise ValueError('Invalid email address format')
        
        return email

class ReportResponse(BaseModel):
    """Model for report generation responses"""
    success: bool
    message: str
    report_id: Optional[str] = None
    
class ReportStatus(BaseModel):
    """Model for report status responses"""
    report_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    message: str
    progress: Optional[int] = None  # 0-100 percentage
