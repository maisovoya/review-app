import re
import string

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


STOP_WORDS = set(ENGLISH_STOP_WORDS)
PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


def preprocess_text(text: str) -> str:
    text = text.lower().translate(PUNCTUATION_TABLE)
    tokens = tokenize(text)
    filtered_tokens = [token for token in tokens if token not in STOP_WORDS]
    return " ".join(filtered_tokens)


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text)
