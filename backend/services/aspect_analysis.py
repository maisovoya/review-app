import re
from typing import Literal, TypedDict


AspectSentiment = Literal["positive", "negative", "neutral"]


class AspectResult(TypedDict):
    sentiment: AspectSentiment
    score: float


ASPECT_KEYWORDS = {
    "quality": {
        "positive": [
            "качественный",
            "хорошее качество",
            "прочный",
            "надежный",
            "отличный материал",
        ],
        "negative": [
            "плохое качество",
            "сломался",
            "брак",
            "дефект",
            "хлипкий",
            "некачественный",
        ],
    },
    "delivery": {
        "positive": [
            "быстрая доставка",
            "пришло быстро",
            "доставили вовремя",
        ],
        "negative": [
            "долго шло",
            "задержка",
            "опоздала доставка",
            "доставка ужасная",
        ],
    },
    "packaging": {
        "positive": [
            "хорошо упаковано",
            "упаковка целая",
        ],
        "negative": [
            "упаковка повреждена",
            "коробка мятая",
            "пришло разбитое",
            "порванная упаковка",
        ],
    },
    "price": {
        "positive": [
            "хорошая цена",
            "стоит своих денег",
            "выгодно",
        ],
        "negative": [
            "дорого",
            "не стоит своих денег",
            "завышенная цена",
        ],
    },
    "usability": {
        "positive": [
            "удобно",
            "легко использовать",
            "понятно",
        ],
        "negative": [
            "неудобно",
            "сложно использовать",
            "непонятно",
        ],
    },
    "support": {
        "positive": [
            "поддержка помогла",
            "быстро ответили",
        ],
        "negative": [
            "поддержка не отвечает",
            "не помогли",
            "игнорируют",
        ],
    },
}


def analyze_aspects(text: str) -> dict[str, AspectResult]:
    """Detect sentiment for business aspects using a lightweight keyword MVP."""
    normalized_text = normalize_text(text)
    results: dict[str, AspectResult] = {}

    for aspect, keyword_groups in ASPECT_KEYWORDS.items():
        positive_count = count_keyword_matches(
            mask_keywords(normalized_text, keyword_groups["negative"]),
            keyword_groups["positive"],
        )
        negative_count = count_keyword_matches(
            normalized_text,
            keyword_groups["negative"],
        )
        results[aspect] = build_aspect_result(positive_count, negative_count)

    return results


def build_aspect_result(positive_count: int, negative_count: int) -> AspectResult:
    """Convert positive/negative keyword hits into a sentiment label and score."""
    total = positive_count + negative_count
    if total == 0:
        return {"sentiment": "neutral", "score": 0.0}

    if positive_count > negative_count:
        return {"sentiment": "positive", "score": round(positive_count / total, 2)}

    if negative_count > positive_count:
        return {"sentiment": "negative", "score": round(negative_count / total, 2)}

    return {"sentiment": "neutral", "score": 0.5}


def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Count exact phrase hits with word boundaries to avoid nested false matches."""
    return sum(1 for keyword in keywords if keyword_in_text(text, keyword))


def keyword_in_text(text: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)
    pattern = rf"(?<![\wа-яё]){re.escape(normalized_keyword)}(?![\wа-яё])"
    return re.search(pattern, text) is not None


def mask_keywords(text: str, keywords: list[str]) -> str:
    masked_text = text
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        pattern = rf"(?<![\wа-яё]){re.escape(normalized_keyword)}(?![\wа-яё])"
        masked_text = re.sub(pattern, " ", masked_text)
    return masked_text


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()
