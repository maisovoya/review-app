from collections import Counter

from sqlalchemy.orm import Session

from backend.models.review import Review
from backend.services.preprocessing import preprocess_text
from backend.services.sentiment import analyze_sentiment


def create_review_records(db: Session, rows: list[dict]) -> int:
    review_objects = []
    for row in rows:
        original_text = row["review"].strip()
        processed_text = preprocess_text(original_text)
        sentiment, score = analyze_sentiment(original_text)
        review_objects.append(
            Review(
                original_text=original_text,
                processed_text=processed_text,
                sentiment=sentiment,
                score=score,
            )
        )

    db.add_all(review_objects)
    db.commit()
    return len(review_objects)


def fetch_reviews(db: Session) -> list[Review]:
    return db.query(Review).order_by(Review.created_at.desc()).all()


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
