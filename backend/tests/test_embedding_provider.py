from app.embedding_provider import EmbeddingProvider

def test_embedding_provider_returns_model_identity():
    name, vector = EmbeddingProvider().embed_text("hello")
    assert name == "local-hash-v2"
    assert len(vector) == 32
