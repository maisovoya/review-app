from backend.services.marketplaces.base import MarketplaceClient
from backend.services.marketplaces.ozon import OzonClient
from backend.services.marketplaces.wildberries import WildberriesClient
from backend.services.marketplaces.yandex_market import YandexMarketClient


def get_marketplace_client(name: str) -> MarketplaceClient:
    clients = {
        "wildberries": WildberriesClient(),
        "ozon": OzonClient(),
        "yandex_market": YandexMarketClient(),
    }

    if name not in clients:
        raise ValueError(f"Unsupported marketplace: {name}")

    return clients[name]
