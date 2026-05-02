from datetime import datetime

import httpx

from backend.schemas.review import NormalizedReviewIn
from backend.services.marketplaces.base import MarketplaceClient


class WildberriesClient(MarketplaceClient):
    marketplace_name = "wildberries"
    base_url = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"

    def fetch_reviews(
        self,
        product_id: str,
        date_from=None,
        date_to=None,
    ) -> list[NormalizedReviewIn]:
        api_key = self.require_env("WB_API_TOKEN")
        start, end = self.build_date_range(date_from, date_to)
        collected_reviews: list[NormalizedReviewIn] = []

        for is_answered in (True, False):
            collected_reviews.extend(
                self._fetch_by_answer_state(
                    api_key=api_key,
                    product_id=product_id,
                    start=start,
                    end=end,
                    is_answered=is_answered,
                )
            )

        return collected_reviews

    def _fetch_by_answer_state(
        self,
        api_key: str,
        product_id: str,
        start,
        end,
        is_answered: bool,
    ) -> list[NormalizedReviewIn]:
        take = 100
        skip = 0
        collected_reviews: list[NormalizedReviewIn] = []

        headers = {"Authorization": api_key}

        with httpx.Client(timeout=30.0, headers=headers) as client:
            while True:
                params = {
                    "isAnswered": str(is_answered).lower(),
                    "nmId": product_id,
                    "take": take,
                    "skip": skip,
                    "order": "dateDesc",
                }
                if start:
                    params["dateFrom"] = int(start.timestamp())
                if end:
                    params["dateTo"] = int(end.timestamp())

                response = client.get(self.base_url, params=params)
                response.raise_for_status()
                payload = response.json()
                reviews = payload.get("data", {}).get("feedbacks", [])

                if not reviews:
                    break

                for review in reviews:
                    review_text = (review.get("text") or "").strip()
                    if not review_text:
                        continue

                    created_at = parse_iso_datetime(review.get("createdDate"))
                    collected_reviews.append(
                        NormalizedReviewIn(
                            external_review_id=str(review.get("id")),
                            product_id=str(
                                review.get("productDetails", {}).get("nmId") or product_id
                            ),
                            marketplace=self.marketplace_name,
                            text=review_text,
                            rating=review.get("productValuation"),
                            review_date=created_at,
                            author=review.get("userName"),
                            source_url=None,
                        )
                    )

                if len(reviews) < take:
                    break
                skip += take

        return collected_reviews


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
