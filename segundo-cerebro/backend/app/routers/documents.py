"""Endpoints de documentos: subir, listar, ver detalle."""
import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.embeddings import EmbeddingProvider
from app.ingestion import ingest_document
from app.main_state import get_embedder
from app.models import Document, DocumentChunk
from app.projects import get_or_create_default_project
from app.schemas import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile,
    folder_hint: str | None = None,
    db: Session = Depends(get_db),
    embedder: EmbeddingProvider = Depends(get_embedder),
):
    if file.size and file.size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Archivo mayor a {settings.max_upload_mb}MB")

    project = get_or_create_default_project(db)

    suffix = os.path.splitext(file.filename or "documento")[1]
    os.makedirs(settings.originals_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.originals_dir) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        doc = ingest_document(
            db,
            project_id=project.id,
            file_path=tmp_path,
            original_filename=file.filename or os.path.basename(tmp_path),
            folder_hint=folder_hint,
            embedder=embedder,
            actor="marlon:upload",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Fallo al procesar el documento: {exc}") from exc
    finally:
        # En un despliegue en la nube (Render) el disco es efímero — no
        # vale la pena conservar esta copia temporal más allá de la
        # ingesta (el original de verdad sigue siendo tuyo, en tu propia
        # carpeta). Guardar el archivo de forma permanente y citable
        # (para "clic en la fuente → ver el documento") es una extensión
        # de Fase 1+ que agrega almacenamiento de objetos — no es parte
        # de la Fase 0.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return _to_out(db, doc)


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    project = get_or_create_default_project(db)
    docs = (
        db.query(Document)
        .filter(Document.project_id == project.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_to_out(db, d) for d in docs]


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    return _to_out(db, doc)


def _to_out(db: Session, doc: Document) -> DocumentOut:
    chunk_count = db.query(func.count(DocumentChunk.id)).filter(DocumentChunk.document_id == doc.id).scalar()
    return DocumentOut(
        id=doc.id,
        original_filename=doc.original_filename,
        doc_type=doc.doc_type.value if doc.doc_type else None,
        doc_code=doc.doc_code,
        discipline=doc.discipline,
        level_zone=doc.level_zone,
        doc_date=doc.doc_date,
        classification_confidence=doc.classification_confidence,
        classification_source=doc.classification_source.value if doc.classification_source else None,
        status=doc.status.value,
        error_message=doc.error_message,
        chunk_count=chunk_count or 0,
        created_at=doc.created_at,
    )
