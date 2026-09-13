from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import DocumentChunkModel, DocumentModel
from app.embeddings import embed_text, EMBEDDING_MODEL
from hashlib import sha256
import math


def split_text(content: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")
    normalized = "\n".join(line.rstrip() for line in content.replace("\r\n", "\n").splitlines()).strip()
    if not normalized:
        return []
    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(normalized), step):
        chunk = normalized[start:start + chunk_size]
        if not chunk:
            break
        chunks.append(chunk)
        if start + chunk_size >= len(normalized):
            break
    return chunks


def create_document(db: Session, filename: str, content: str) -> DocumentModel:
    chunks = split_text(content)
    if not filename.strip() or not content.strip():
        raise ValueError("filename and content are required")
    content_hash = sha256(content.strip().encode("utf-8")).hexdigest()
    existing = db.query(DocumentModel).filter_by(filename=filename.strip(), content=content).first()
    if existing is not None:
        return existing
    document = DocumentModel(filename=filename.strip(), content=content)
    document.chunks = [
        DocumentChunkModel(chunk_index=index, content=chunk, metadata_json={"source": filename.strip(), "content_hash": content_hash}, embedding=embed_text(chunk), embedding_model=EMBEDDING_MODEL, embedding_dim=32)
        for index, chunk in enumerate(chunks)
    ]
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def search_documents(db: Session, query: str, limit: int = 5) -> list[dict]:
    normalized = query.strip()
    if not normalized:
        raise ValueError("query is required")
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    chunks = db.scalars(select(DocumentChunkModel).join(DocumentModel)).all()
    terms = [term.lower() for term in normalized.split() if term]
    # Chinese questions are commonly written without spaces. Use overlapping
    # bigrams so phrases such as "我叫什么" can match "我叫彭健豪".
    if len(terms) == 1 and any("\u4e00" <= char <= "\u9fff" for char in terms[0]):
        terms = list(dict.fromkeys([terms[0][index:index + 2] for index in range(len(terms[0]) - 1)] + terms))
    matches = []
    for chunk in chunks:
        haystack = chunk.content.lower()
        score = sum(haystack.count(term) for term in terms)
        normalized_score = score / max(len(terms), 1)
        threshold = 0.15 if any("\u4e00" <= char <= "\u9fff" for char in normalized) else 0.5
        if normalized_score >= threshold:
            matches.append({"document_id": chunk.document_id, "filename": chunk.document.filename, "chunk_index": chunk.chunk_index, "content": chunk.content, "score": round(normalized_score, 4), "metadata": chunk.metadata_json or {}})
    ranked = sorted(matches, key=lambda item: (-item["score"], item["filename"], item["chunk_index"]))
    return ranked[:limit]


def retrieve_relevant_documents(db: Session, query: str, limit: int = 3) -> list[dict]:
    normalized = query.strip().lower()
    if not normalized:
        return []
    # Agent context uses conservative lexical evidence; callers can explicitly
    # request vector mode when semantic recall is desired.
    return search_documents(db, normalized, limit)


def vector_search_documents(db: Session, query: str, limit: int = 5) -> list[dict]:
    normalized = query.strip()
    if not normalized:
        raise ValueError("query is required")
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    query_vector = embed_text(normalized)
    matches = []
    for chunk in db.scalars(select(DocumentChunkModel).join(DocumentModel)).all():
        vector = chunk.embedding or []
        if len(vector) != len(query_vector):
            continue
        score = sum(left * right for left, right in zip(query_vector, vector))
        matches.append({"document_id": chunk.document_id, "filename": chunk.document.filename, "chunk_index": chunk.chunk_index, "content": chunk.content, "score": round(score, 8), "metadata": chunk.metadata_json or {}})
    return sorted(matches, key=lambda item: (-item["score"], item["filename"], item["chunk_index"]))[:limit]
