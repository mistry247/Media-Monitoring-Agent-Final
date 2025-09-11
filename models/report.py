from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from database import Base

class Report(Base):
    """Model for generated reports"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String, nullable=False)  # 'media' or 'hansard'
    recipient_email = Column(String, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default='pending', nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    content = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

class HansardQuestion(Base):
    """Model for Hansard questions"""
    __tablename__ = 'hansard_questions'
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_articles = Column(Text, nullable=True)  # JSON array of related article IDs

class ProcessedArchive(Base):
    """Model for processed articles archive"""
    __tablename__ = 'processed_archive'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    submitted_by = Column(String, nullable=False)
    processed_date = Column(DateTime, default=datetime.utcnow, nullable=False)