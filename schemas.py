from pydantic import BaseModel
from typing import List

class ManualArticleUpdate(BaseModel):
    id: int
    content: str

class ManualArticleBatchPayload(BaseModel):
    articles: List[ManualArticleUpdate]
    recipient_email: str
