from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from backend.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=False)
    sentiment = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
