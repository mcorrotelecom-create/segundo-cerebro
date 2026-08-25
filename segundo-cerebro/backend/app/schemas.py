"""Esquemas de entrada/salida de la API (Pydantic)."""
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    original_filename: str
    doc_type: str | None
    doc_code: str | None
    discipline: str | None
    level_zone: str | None
    doc_date: date | None
    classification_confidence: float
    classification_source: str | None
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchHitOut(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    doc_type: str | None
    doc_code: str | None
    text: str
    source_ref: dict[str, Any]
    score: float
    match_type: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHitOut]
