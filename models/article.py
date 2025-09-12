from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from datetime import datetime
from database import Base

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    submitted_by = Column(String, nullable=False)
    pasted_text = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ManualInputArticle(Base):
    __tablename__ = 'manual_input_articles'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    submitted_by = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    article_content = Column(Text, nullable=True)