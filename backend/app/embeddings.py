import hashlib
import math

EMBEDDING_MODEL = "local-hash-v2"


def _tokens(text: str) -> list[str]:
    normalized = text.lower().strip()
    if any("\u4e00" <= char <= "\u9fff" for char in normalized):
        chars = [char for char in normalized if not char.isspace()]
        return chars + ["".join(chars[index:index + 2]) for index in range(len(chars) - 1)]
    return normalized.split()


def embed_text(text: str, dimensions: int = 32) -> list[float]:
    """Generate a deterministic local vector until a remote provider is configured."""
    if dimensions < 1:
        raise ValueError("dimensions must be positive")
    vector = [0.0] * dimensions
    words = _tokens(text)
    for word in words:
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        for index in range(dimensions):
            vector[index] += (digest[index % len(digest)] / 255.0) * 2 - 1
    norm = math.sqrt(sum(value * value for value in vector))
    return [round(value / norm, 8) for value in vector] if norm else vector
