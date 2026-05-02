from collections import Counter
from datetime import date, datetime, time
import json
from typing import Any

from sqlalchemy.orm import Session

from backend.models.review import Review
from backend.schemas.review import NormalizedReviewIn
from backend.services.aspect_analysis import ASPECT_KEYWORDS, analyze_aspects
from backend.services.preprocessing import preprocess_text
from backend.services.sentiment import analyze_sentiment


def normalize_csv_reviews(rows: list[dict[str, Any]]) -> list[NormalizedReviewIn]:
    normalized_reviews = []
    for index, row in enumerate(rows, start=1):
        review_text = clean_optional_string(row.get("review"))
        if not review_text:
            continue

        normalized_reviews.append(
            NormalizedReviewIn(
                external_review_id=clean_optional_string(
                    row.get("external_review_id") or row.get("id")
                )
                or f"csv-{index}",
                product_id=clean_optional_string(row.get("product_id")),
                marketplace=clean_optional_string(row.get("marketplace")) or "csv",
                text=review_text,
                rating=parse_optional_int(row.get("rating")),
                review_date=parse_optional_datetime(row.get("review_date")),
                author=clean_optional_string(row.get("author")),
                source_url=clean_optional_string(row.get("source_url")),
            )
        )

    return normalized_reviews


def save_reviews(db: Session, reviews: list[NormalizedReviewIn]) -> int:
    review_objects = []
    for review in reviews:
        if review.external_review_id and review.marketplace != "csv":
            existing_review = (
                db.query(Review.id)
                .filter(
                    Review.marketplace == review.marketplace,
                    Review.external_review_id == review.external_review_id,
                )
                .first()
            )
            if existing_review:
                continue

        original_text = review.text.strip()
        processed_text = preprocess_text(original_text)
        sentiment_result = analyze_sentiment(original_text)
        aspects = analyze_aspects(original_text)
        review_objects.append(
            Review(
                product_id=review.product_id,
                marketplace=review.marketplace,
                external_review_id=review.external_review_id,
                original_text=original_text,
                processed_text=processed_text,
                rating=review.rating,
                review_date=review.review_date,
                author=review.author,
                source_url=review.source_url,
                sentiment=sentiment_result.label,
                score=sentiment_result.score,
                aspects=json.dumps(aspects, ensure_ascii=False),
            )
        )

    if not review_objects:
        return 0

    db.add_all(review_objects)
    db.commit()
    return len(review_objects)


def fetch_reviews(db: Session) -> list[Review]:
    return db.query(Review).order_by(Review.created_at.desc()).all()


def delete_review(db: Session, review_id: int) -> bool:
    """Delete one review so it no longer participates in analytics."""
    review = db.get(Review, review_id)
    if review is None:
        return False

    db.delete(review)
    db.commit()
    return True


def calculate_sentiment_stats(db: Session) -> dict:
    reviews = db.query(Review).all()
    total = len(reviews)
    counts = Counter(review.sentiment for review in reviews)

    if total == 0:
        return {
            "total_reviews": 0,
            "positive_percentage": 0.0,
            "negative_percentage": 0.0,
            "neutral_percentage": 0.0,
        }

    return {
        "total_reviews": total,
        "positive_percentage": round(counts.get("positive", 0) / total * 100, 2),
        "negative_percentage": round(counts.get("negative", 0) / total * 100, 2),
        "neutral_percentage": round(counts.get("neutral", 0) / total * 100, 2),
    }


def get_top_problems(db: Session, limit: int = 5) -> dict:
    """Count the most frequent negative aspect mentions across saved reviews."""
    aspect_counts = Counter()

    for review in db.query(Review.aspects).all():
        aspects = parse_aspects_json(review.aspects)
        for aspect in ASPECT_KEYWORDS:
            result = aspects.get(aspect)
            if isinstance(result, dict) and result.get("sentiment") == "negative":
                aspect_counts[aspect] += 1

    total_negative_mentions = sum(aspect_counts.values())
    problems = []

    for aspect, count in aspect_counts.most_common(limit):
        percentage = (
            round(count / total_negative_mentions * 100, 2)
            if total_negative_mentions
            else 0.0
        )
        problems.append(
            {
                "aspect": aspect,
                "count": count,
                "percentage": percentage,
            }
        )

    return {
        "total_negative_aspect_mentions": total_negative_mentions,
        "problems": problems,
    }


def parse_aspects_json(value: str | None) -> dict:
    """Safely parse stored aspect JSON and tolerate old or corrupted rows."""
    if not value:
        return {}

    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def clean_optional_string(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def parse_optional_int(value: Any) -> int | None:
    cleaned = clean_optional_string(value)
    if cleaned is None:
        return None

    try:
        return int(cleaned)
    except (TypeError, ValueError):
        return None


def parse_optional_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    normalized = str(value).strip()
    if not normalized:
        return None

    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
