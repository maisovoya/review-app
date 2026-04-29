from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from transformers import pipeline

try:
    from nltk.stem.snowball import RussianStemmer
except Exception:  # noqa: BLE001
    RussianStemmer = None


# Лучше для русских отзывов
MODEL_NAME = "cointegrated/rubert-tiny-sentiment-balanced"

# Альтернатива:
# MODEL_NAME = "seara/rubert-tiny2-russian-sentiment"


RUSSIAN_POSITIVE_WORDS = {
    "отличн", "прекрасн", "хорош", "супер", "класс", "любл", "довол",
    "рекоменд", "идеальн", "качествен", "быстр", "удобн", "приятн",
    "замечат", "порад", "крут",
}

RUSSIAN_NEGATIVE_WORDS = {
    "ужасн", "плох", "слом", "разочаров", "ненавиж", "бесполезн", "худш",
    "отврат", "медлен", "дорог", "неудобн", "груб", "проблем", "брак",
    "кошмар", "жалоб", "обман",
}

NEGATIONS = {
    "не", "нет", "ни", "никогда", "вовсе", "совсем"
}

INTENSIFIERS = {
    "очень": 1.4,
    "крайне": 1.5,
    "сильно": 1.3,
    "слишком": 1.2,
    "довольно": 1.15,
    "весьма": 1.2,
    "реально": 1.15,
}

LABEL_MAP = {
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
    "label_0": "negative",
    "label_1": "neutral",
    "label_2": "positive",
    # на случай русских названий
    "негативный": "negative",
    "нейтральный": "neutral",
    "позитивный": "positive",
}


@dataclass(frozen=True)
class SentimentResult:
    label: str
    score: float
    probabilities: dict[str, float]
    method: str


@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    # return_all_scores / top_k=None позволяет получить распределение по классам
    return pipeline(
        task="text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        truncation=True,
        top_k=None,
    )


@lru_cache(maxsize=1)
def get_stemmer():
    if RussianStemmer is None:
        return None
    return RussianStemmer()


def normalize_label(label: str) -> str:
    return LABEL_MAP.get(label.lower().strip(), "neutral")


def tokenize_ru(text: str) -> list[str]:
    return re.findall(r"[а-яёa-z]+", text.lower())


def stem_word(word: str) -> str:
    stemmer = get_stemmer()
    if stemmer is None:
        return word
    return stemmer.stem(word)


def split_into_chunks(text: str, max_chars: int = 400, overlap: int = 80) -> list[str]:
    """
    Грубое, но практичное разбиение длинного отзыва.
    Для отзывов часто достаточно чанков по предложениям/символам.
    """
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []

    if len(clean) <= max_chars:
        return [clean]

    sentences = re.split(r"(?<=[.!?])\s+", clean)
    chunks: list[str] = []
    current = ""

    for sent in sentences:
        if not sent:
            continue

        if len(current) + len(sent) + 1 <= max_chars:
            current = f"{current} {sent}".strip()
        else:
            if current:
                chunks.append(current)
            if len(sent) <= max_chars:
                current = sent
            else:
                # если одно предложение очень длинное
                step = max_chars - overlap
                for i in range(0, len(sent), step):
                    part = sent[i:i + max_chars].strip()
                    if part:
                        chunks.append(part)
                current = ""

    if current:
        chunks.append(current)

    return chunks


def aggregate_probabilities(chunk_probs: Iterable[dict[str, float]]) -> dict[str, float]:
    """
    Усреднение вероятностей по чанкам.
    Можно потом заменить на взвешивание по длине чанка.
    """
    totals = {"negative": 0.0, "neutral": 0.0, "positive": 0.0}
    count = 0

    for probs in chunk_probs:
        count += 1
        for label in totals:
            totals[label] += probs.get(label, 0.0)

    if count == 0:
        return {"negative": 0.0, "neutral": 1.0, "positive": 0.0}

    return {k: round(v / count, 6) for k, v in totals.items()}


def probs_to_result(probs: dict[str, float], method: str) -> SentimentResult:
    label = max(probs, key=probs.get)
    score = round(float(probs[label]), 4)
    return SentimentResult(
        label=label,
        score=score,
        probabilities={k: round(float(v), 4) for k, v in probs.items()},
        method=method,
    )


def analyze_sentiment(text: str) -> SentimentResult:
    text = text.strip()
    if not text:
        return SentimentResult(
            label="neutral",
            score=1.0,
            probabilities={"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            method="empty",
        )

    try:
        classifier = get_sentiment_pipeline()
        chunks = split_into_chunks(text)

        all_chunk_probs: list[dict[str, float]] = []

        for chunk in chunks:
            raw = classifier(chunk)
            # pipeline(top_k=None) обычно возвращает [[...]] для одного текста
            if raw and isinstance(raw[0], list):
                raw = raw[0]

            probs = {"negative": 0.0, "neutral": 0.0, "positive": 0.0}
            for item in raw:
                label = normalize_label(item["label"])
                probs[label] = float(item["score"])

            # на всякий случай нормализуем
            total = sum(probs.values()) or 1.0
            probs = {k: v / total for k, v in probs.items()}
            all_chunk_probs.append(probs)

        final_probs = aggregate_probabilities(all_chunk_probs)
        return probs_to_result(final_probs, method="model")

    except Exception:
        return analyze_sentiment_fallback(text)


def analyze_sentiment_fallback(text: str) -> SentimentResult:
    """
    Более умный fallback:
    - нормальная токенизация;
    - учёт отрицаний;
    - усилители;
    - стемминг для русского.
    """
    tokens = tokenize_ru(text)
    if not tokens:
        return SentimentResult(
            label="neutral",
            score=0.5,
            probabilities={"negative": 0.25, "neutral": 0.5, "positive": 0.25},
            method="fallback",
        )

    stems = [stem_word(t) for t in tokens]

    pos_score = 0.0
    neg_score = 0.0

    for i, stem in enumerate(stems):
        multiplier = 1.0

        # усилитель слева
        if i > 0 and tokens[i - 1] in INTENSIFIERS:
            multiplier *= INTENSIFIERS[tokens[i - 1]]

        # отрицание в окне 2 слова слева
        negated = any(tok in NEGATIONS for tok in tokens[max(0, i - 2):i])

        if stem in RUSSIAN_POSITIVE_WORDS:
            if negated:
                neg_score += 1.0 * multiplier
            else:
                pos_score += 1.0 * multiplier

        elif stem in RUSSIAN_NEGATIVE_WORDS:
            if negated:
                pos_score += 0.8 * multiplier
            else:
                neg_score += 1.0 * multiplier

    # Небольшой бонус/штраф по знакам
    exclamations = text.count("!")
    if exclamations:
        if pos_score > neg_score:
            pos_score += min(exclamations * 0.1, 0.3)
        elif neg_score > pos_score:
            neg_score += min(exclamations * 0.1, 0.3)

    total = pos_score + neg_score

    if total == 0:
        probs = {"negative": 0.2, "neutral": 0.6, "positive": 0.2}
        return probs_to_result(probs, method="fallback")

    # Чем меньше разница, тем больше neutral
    diff = abs(pos_score - neg_score)
    strength = min(total / 3.0, 1.0)
    neutrality = max(0.1, 1.0 - min(diff / max(total, 1e-6), 1.0) * strength)

    if pos_score > neg_score:
        pos = 0.55 + min(diff / (total + 1e-6), 0.35)
        neg = 1.0 - pos - neutrality
    elif neg_score > pos_score:
        neg = 0.55 + min(diff / (total + 1e-6), 0.35)
        pos = 1.0 - neg - neutrality
    else:
        pos = 0.2
        neg = 0.2
        neutrality = 0.6

    probs = {
        "negative": max(0.0, neg),
        "neutral": max(0.0, neutrality),
        "positive": max(0.0, pos),
    }

    # финальная нормализация
    s = sum(probs.values()) or 1.0
    probs = {k: v / s for k, v in probs.items()}

    return probs_to_result(probs, method="fallback")