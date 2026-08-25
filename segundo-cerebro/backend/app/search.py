"""Búsqueda híbrida: texto completo (Postgres, español) + similitud
semántica (coseno en memoria). Ver §09 de la propuesta técnica.
"""
from dataclasses import dataclass
from typing import Any

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.embeddings import EmbeddingProvider
from app.models import Document, DocumentChunk
from app.vectorstore import top_k_cosine


@dataclass
class SearchHit:
    chunk_id: str
    document_id: str
    document_filename: str
    doc_type: str | None
    doc_code: str | None
    text: str
    source_ref: dict[str, Any]
    score: float
    match_type: str  # "semantico" | "texto_completo" | "ambos"


def hybrid_search(
    db: Session, *, project_id: str, query: str, embedder: EmbeddingProvider, limit: int = 10
) -> list[SearchHit]:
    semantic_hits = _semantic_search(db, project_id=project_id, query=query, embedder=embedder, limit=limit)
    keyword_hits = _keyword_search(db, project_id=project_id, query=query, limit=limit)

    merged: dict[str, SearchHit] = {}
    for hit in semantic_hits:
        merged[hit.chunk_id] = hit
    for hit in keyword_hits:
        if hit.chunk_id in merged:
            merged[hit.chunk_id].match_type = "ambos"
            merged[hit.chunk_id].score = max(merged[hit.chunk_id].score, hit.score)
        else:
            merged[hit.chunk_id] = hit

    results = sorted(merged.values(), key=lambda h: h.score, reverse=True)
    return results[:limit]


def _semantic_search(
    db: Session, *, project_id: str, query: str, embedder: EmbeddingProvider, limit: int
) -> list[SearchHit]:
    rows = (
        db.query(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.project_id == project_id)
        .all()
    )
    if not rows:
        return []

    matrix = np.array([r[0].embedding for r in rows], dtype=np.float32)
    query_vec = embedder.embed([query])[0]
    top = top_k_cosine(query_vec, matrix, k=limit)

    hits = []
    for idx, score in top:
        chunk, doc = rows[idx]
        hits.append(
            SearchHit(
                chunk_id=chunk.id,
                document_id=doc.id,
                document_filename=doc.original_filename,
                doc_type=doc.doc_type.value if doc.doc_type else None,
                doc_code=doc.doc_code,
                text=chunk.text,
                source_ref=chunk.source_ref,
                score=score,
                match_type="semantico",
            )
        )
    return hits


def _keyword_search(db: Session, *, project_id: str, query: str, limit: int) -> list[SearchHit]:
    sql = text(
        """
        SELECT c.id, c.document_id, d.original_filename, d.doc_type, d.doc_code,
               c.text, c.source_ref,
               ts_rank(to_tsvector('spanish', c.text), plainto_tsquery('spanish', :q)) AS rank
        FROM document_chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.project_id = :project_id
          AND to_tsvector('spanish', c.text) @@ plainto_tsquery('spanish', :q)
        ORDER BY rank DESC
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"q": query, "project_id": project_id, "limit": limit}).fetchall()
    hits = []
    for row in rows:
        hits.append(
            SearchHit(
                chunk_id=row.id,
                document_id=row.document_id,
                document_filename=row.original_filename,
                doc_type=row.doc_type,
                doc_code=row.doc_code,
                text=row.text,
                source_ref=row.source_ref,
                score=float(row.rank),
                match_type="texto_completo",
            )
        )
    return hits
