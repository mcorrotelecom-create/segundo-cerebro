"""Orquesta el pipeline completo: clasificar → extraer → trocear → embeber
→ persistir. Ver §06 de la propuesta técnica.

Esta función es la única puerta de entrada para que un documento entre al
sistema — tanto la subida manual desde la interfaz como, más adelante, un
watcher de carpeta, pasan por aquí.
"""
import hashlib
import logging
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.chunking import chunk_units
from app.classification import classify_filename
from app.embeddings import EmbeddingProvider
from app.enums import DocumentStatus
from app.extraction import extract
from app.models import AuditLog, Document, DocumentChunk

logger = logging.getLogger(__name__)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def ingest_document(
    db: Session,
    *,
    project_id: str,
    file_path: str,
    original_filename: str,
    folder_hint: str | None,
    embedder: EmbeddingProvider,
    actor: str = "ai:ingestion",
) -> Document:
    """Ingiere un único documento. Lanza excepción si algo falla, dejando el
    registro en estado ERROR con el mensaje — nunca falla en silencio.
    """
    file_ext = os.path.splitext(original_filename)[1].lstrip(".").lower()
    byte_size = os.path.getsize(file_path)
    file_hash = _sha256_file(file_path)

    existing = (
        db.query(Document)
        .filter(Document.project_id == project_id, Document.storage_path == file_path)
        .one_or_none()
    )
    if existing and existing.file_hash == file_hash and existing.status == DocumentStatus.INDEXED:
        logger.info("Documento sin cambios, se omite: %s", original_filename)
        return existing

    classification = classify_filename(original_filename, folder_hint)

    doc = existing or Document(project_id=project_id, storage_path=file_path)
    doc.original_filename = original_filename
    doc.file_ext = file_ext
    doc.byte_size = byte_size
    doc.file_hash = file_hash
    doc.doc_type = classification.doc_type
    doc.doc_code = classification.doc_code
    doc.discipline = classification.discipline
    doc.level_zone = classification.level_zone
    doc.doc_date = classification.doc_date
    doc.classification_confidence = classification.confidence
    doc.classification_source = classification.source
    doc.status = DocumentStatus.PROCESSING
    doc.error_message = None
    db.add(doc)
    db.flush()  # asigna doc.id sin cerrar la transacción

    try:
        units = extract(file_path, file_ext)
        chunks = chunk_units(units)

        # limpia fragmentos previos si es una re-ingesta
        if existing:
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

        if chunks:
            vectors = embedder.embed([c.text for c in chunks])
            for i, (c, vec) in enumerate(zip(chunks, vectors)):
                db.add(
                    DocumentChunk(
                        document_id=doc.id,
                        chunk_index=i,
                        text=c.text,
                        source_ref=c.source_ref,
                        embedding=vec.tolist(),
                    )
                )

        doc.status = DocumentStatus.INDEXED
        doc.indexed_at = datetime.now(timezone.utc)
        db.add(
            AuditLog(
                actor=actor,
                action="document.ingested",
                entity_type="document",
                entity_id=doc.id,
                after={
                    "doc_type": classification.doc_type.value,
                    "confidence": classification.confidence,
                    "chunks": len(chunks),
                },
                document_id=doc.id,
            )
        )
        db.commit()
        db.refresh(doc)
        return doc

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        doc.status = DocumentStatus.ERROR
        doc.error_message = str(exc)
        db.add(doc)
        db.commit()
        logger.exception("Fallo al ingerir %s", original_filename)
        raise
