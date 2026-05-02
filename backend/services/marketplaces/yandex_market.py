from datetime import datetime

import httpx

from backend.schemas.review import NormalizedReviewIn
from backend.services.marketplaces.base import MarketplaceClient


class YandexMarketClient(MarketplaceClient):
    marketplace_name = "yandex_market"
    base_url_template = "https://api.partner.market.yandex.ru/v2/businesses/{business_id}/goods-feedback"

    def fetch_reviews(
        self,
        product_id: str,
        date_from=None,
        date_to=None,
    ) -> list[NormalizedReviewIn]:
        business_id = self.require_env("YANDEX_MARKET_BUSINESS_ID")
        api_key = self.require_env("YANDEX_MARKET_API_KEY")
        start, end = self.build_date_range(date_from, date_to)
        page_token = None
        collected_reviews: list[NormalizedReviewIn] = []

        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json",
        }
        url = self.base_url_template.format(business_id=business_id)

        with httpx.Client(timeout=30.0, headers=headers) as client:
            while True:
                body = {
                    "offerIds": [product_id],
                }
                if start:
                    body["dateTimeFrom"] = start.isoformat()
                if end:
                    body["dateTimeTo"] = end.isoformat()
                if page_token:
                    body["page_token"] = page_token

                response = client.post(url, json=body)
                response.raise_for_status()
                payload = response.json()
                reviews = payload.get("result", {}).get("feedbacks", [])

                for review in reviews:
                    text_parts = [
                        review.get("description", {}).get("advantages"),
                        review.get("description", {}).get("comment"),
                        review.get("description", {}).get("disadvantages"),
                    ]
                    normalized_text = "\n".join(part.strip() for part in text_parts if part and part.strip())
                    if not normalized_text:
                        continue

                    collected_reviews.append(
                        NormalizedReviewIn(
                            external_review_id=str(review.get("feedbackId")),
                            product_id=(
                                review.get("identifiers", {}).get("offerId") or product_id
                            ),
                            marketplace=self.marketplace_name,
                            text=normalized_text,
                            rating=review.get("statistics", {}).get("rating"),
                            review_date=parse_iso_datetime(review.get("createdAt")),
                            author=review.get("author"),
                            source_url=None,
                        )
                    )

                page_token = payload.get("result", {}).get("paging", {}).get("nextPageToken")
                if not page_token:
                    break

        return collected_reviews


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
