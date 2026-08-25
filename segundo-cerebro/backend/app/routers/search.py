"""Endpoint de búsqueda híbrida."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.embeddings import EmbeddingProvider
from app.main_state import get_embedder
from app.projects import get_or_create_default_project
from app.schemas import SearchHitOut, SearchResponse
from app.search import hybrid_search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    embedder: EmbeddingProvider = Depends(get_embedder),
):
    project = get_or_create_default_project(db)
    hits = hybrid_search(db, project_id=project.id, query=q, embedder=embedder, limit=limit)
    return SearchResponse(
        query=q,
        results=[
            SearchHitOut(
                chunk_id=h.chunk_id,
                document_id=h.document_id,
                document_filename=h.document_filename,
                doc_type=h.doc_type,
                doc_code=h.doc_code,
                text=h.text,
                source_ref=h.source_ref,
                score=h.score,
                match_type=h.match_type,
            )
            for h in hits
        ],
    )
