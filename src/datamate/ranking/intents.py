"""Rank intent descriptions using a fixed lexical index."""

from dataclasses import dataclass
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


@dataclass(frozen=True)
class IntentMatch:
    intent: str
    score: float


class IntentIndex:
    def __init__(self, descriptions: tuple[tuple[str, str], ...]):
        self.intents = tuple(intent for intent, _ in descriptions)
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))
        self.vectors = self.vectorizer.fit_transform([normalize_text(text) for _, text in descriptions])

    def rank(self, question: str) -> list[IntentMatch]:
        query = self.vectorizer.transform([normalize_text(question)])
        scores = cosine_similarity(query, self.vectors)[0]
        best: dict[str, float] = {}
        for intent, score in zip(self.intents, scores):
            best[intent] = max(best.get(intent, 0.0), float(score))
        return sorted((IntentMatch(key, score) for key, score in best.items()),
                      key=lambda match: -match.score)
