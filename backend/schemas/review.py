from datetime import datetime

from pydantic import BaseModel


class ReviewOut(BaseModel):
    id: int
    original_text: str
    processed_text: str
    sentiment: str
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_reviews: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float


class UploadResponse(BaseModel):
    message: str
    count: int
