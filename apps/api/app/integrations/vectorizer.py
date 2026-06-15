import hashlib
import math


class HashVectorizer:
    """Small dependency-free embedding fallback.

    This is not as semantically strong as a model embedding, but it gives Qdrant
    a stable vector contract until you plug in Gemini/OpenAI embeddings.
    """

    def __init__(self, size: int) -> None:
        self.size = size

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.size
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.size
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

