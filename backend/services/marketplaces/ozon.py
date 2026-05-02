from backend.schemas.review import NormalizedReviewIn
from backend.services.marketplaces.base import MarketplaceClient


class OzonClient(MarketplaceClient):
    marketplace_name = "ozon"

    def fetch_reviews(
        self,
        product_id: str,
        date_from=None,
        date_to=None,
    ) -> list[NormalizedReviewIn]:
        raise NotImplementedError(
            "Ozon review collection is not enabled in this prototype. "
            "Use an official seller export or add a confirmed seller API method first."
        )
