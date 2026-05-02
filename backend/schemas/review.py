import json
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AspectOut(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    score: float


class ReviewOut(BaseModel):
    id: int
    product_id: str | None = None
    marketplace: str | None = None
    external_review_id: str | None = None
    original_text: str
    processed_text: str
    rating: int | None = None
    review_date: datetime | None = None
    author: str | None = None
    source_url: str | None = None
    sentiment: str
    score: float
    aspects: dict[str, AspectOut] | None = None
    created_at: datetime

    @field_validator("aspects", mode="before")
    @classmethod
    def parse_aspects(cls, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None

        if not isinstance(value, dict):
            return None

        cleaned = {}
        for aspect, result in value.items():
            if not isinstance(result, dict):
                continue
            sentiment = result.get("sentiment")
            if sentiment not in {"positive", "negative", "neutral"}:
                continue
            try:
                score = float(result.get("score", 0.0))
            except (TypeError, ValueError):
                score = 0.0
            cleaned[aspect] = {
                "sentiment": sentiment,
                "score": score,
            }

        return cleaned

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


class DeleteResponse(BaseModel):
    message: str


class ProblemOut(BaseModel):
    aspect: str
    count: int
    percentage: float


class ProblemsOut(BaseModel):
    total_negative_aspect_mentions: int
    problems: list[ProblemOut]


class InsightsOut(BaseModel):
    summary: str
    recommendations: list[str]
    risk_level: Literal["low", "medium", "high"]


class CollectRequest(BaseModel):
    marketplace: Literal["wildberries", "ozon", "yandex_market"]
    product_id: str = Field(..., min_length=1)
    date_from: date | None = None
    date_to: date | None = None


class NormalizedReviewIn(BaseModel):
    external_review_id: str | None = None
    product_id: str | None = None
    marketplace: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    rating: int | None = None
    review_date: datetime | None = None
    author: str | None = None
    source_url: str | None = None
