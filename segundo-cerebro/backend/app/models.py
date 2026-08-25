"""Modelo de datos — Fase 0.

Esto es un subconjunto deliberado del modelo completo descrito en la
propuesta técnica (§04): projects, documents, document_chunks y audit_log.
Las entidades de negocio (boq_item, progress_account, rfi, submittal, etc.)
se agregan en Fase 1+, cuando el pipeline de ingesta ya es sólido.

Cada tabla de dato derivado lleva sus columnas de procedencia
(source_type / source_ref) desde el día uno — no se agregan después.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import ClassificationSource, DocType, DocumentStatus


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    client: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("project_id", "storage_path", name="uq_document_project_path"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)

    original_filename: Mapped[str] = mapped_column(String(500))
    storage_path: Mapped[str] = mapped_column(Text)  # ruta absoluta al archivo original, nunca se duplica
    file_ext: Mapped[str] = mapped_column(String(10))
    byte_size: Mapped[int] = mapped_column(Integer)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)  # sha256 — detecta cambios en el original

    # --- clasificación ---
    doc_type: Mapped[DocType | None] = mapped_column(Enum(DocType, native_enum=False), nullable=True)
    doc_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ej. "F59", "NOTA ACC-HDN-TEC-1098-2025"
    discipline: Mapped[str | None] = mapped_column(String(50), nullable=True)  # SCI, HVAC, ELECTRICO...
    level_zone: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ej. "N-200"
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    classification_source: Mapped[ClassificationSource | None] = mapped_column(
        Enum(ClassificationSource, native_enum=False), nullable=True
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Un fragmento de texto extraído de un documento, con su embedding y
    su referencia exacta a la fuente (página, hoja+filas, párrafo).

    Nota de diseño: el embedding se guarda como arreglo de floats (Postgres
    FLOAT8[]), no con el tipo `vector` de pgvector. A la escala de un
    proyecto de ingeniería (miles de chunks, no millones), una búsqueda por
    similitud de coseno calculada en la aplicación con NumPy toma
    milisegundos — introducir la extensión pgvector no compra rendimiento
    real a este tamaño y sí agrega una dependencia de infraestructura más.
    Si el corpus crece mucho más allá de esto, es un cambio localizado en
    app/vectorstore.py, no una migración de esquema.
    """

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)

    text: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[dict] = mapped_column(JSON)  # {"page": 3} | {"sheet": "...", "rows": "12-18"} | {"paragraph": 5}
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="chunks")


class AuditLog(Base):
    """Registro inmutable: quién hizo qué, cuándo, antes y después.

    Nunca se actualiza ni se borra una fila de esta tabla — solo se inserta.
    """

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(String(255))  # "marlon" | "ai:ingestion" | "ai:suggestion"
    action: Mapped[str] = mapped_column(String(100))  # "document.ingested" | "document.classified" ...
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(100))
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
