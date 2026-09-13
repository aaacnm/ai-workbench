from app.embeddings import embed_text


def test_embedding_is_deterministic_and_normalized():
    first = embed_text("knowledge retrieval")
    assert first == embed_text("knowledge retrieval")
    assert len(first) == 32
    assert round(sum(value * value for value in first), 5) == 1


def test_chinese_matching_text_is_more_similar_than_unrelated_text():
    target = embed_text("我叫彭健豪，来自杭州")
    related = embed_text("我叫彭健豪")
    unrelated = embed_text("苹果公司发布了新手机")
    related_score = sum(left * right for left, right in zip(target, related))
    unrelated_score = sum(left * right for left, right in zip(target, unrelated))
    assert related_score > unrelated_score
