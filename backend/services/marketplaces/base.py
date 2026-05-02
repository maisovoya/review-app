import os
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timezone

from backend.schemas.review import NormalizedReviewIn


class MarketplaceClient(ABC):
    marketplace_name: str

    @abstractmethod
    def fetch_reviews(
        self,
        product_id: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[NormalizedReviewIn]:
        raise NotImplementedError

    def require_env(self, env_name: str) -> str:
        value = os.getenv(env_name)
        if not value:
            raise ValueError(f"Missing required environment variable: {env_name}")
        return value

    def build_date_range(
        self,
        date_from: date | None,
        date_to: date | None,
    ) -> tuple[datetime | None, datetime | None]:
        start = (
            datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            if date_from
            else None
        )
        end = (
            datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            if date_to
            else None
        )
        return start, end
