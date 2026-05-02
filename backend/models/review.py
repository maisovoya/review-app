from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from backend.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Text, nullable=True, index=True)
    marketplace = Column(Text, nullable=True, index=True)
    external_review_id = Column(Text, nullable=True, index=True)
    original_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    review_date = Column(DateTime, nullable=True)
    author = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    sentiment = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    aspects = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
