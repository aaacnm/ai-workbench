from collections.abc import Callable
from app.embeddings import embed_text

class EmbeddingProvider:
    def __init__(self, name: str = "local-hash-v2", embed: Callable[[str], list[float]] = embed_text):
        self.name = name
        self._embed = embed

    def embed_text(self, text: str) -> tuple[str, list[float]]:
        return self.name, self._embed(text)
