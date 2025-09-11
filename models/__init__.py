# Import all SQLAlchemy models to ensure they're registered with Base
from .article import Article, ManualInputArticle
from .report import Report, HansardQuestion, ProcessedArchive

__all__ = [
    "Article", 
    "ManualInputArticle", 
    "ProcessedArchive", 
    "Report", 
    "HansardQuestion"
]