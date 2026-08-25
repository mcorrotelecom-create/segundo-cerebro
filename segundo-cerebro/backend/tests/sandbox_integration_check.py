"""Prueba de integración de Fase 0, adaptada a las restricciones de RED de
ESTE entorno de desarrollo (sandbox de Claude): no se pudo instalar
FastAPI/SQLAlchemy/psycopg vía pip (PyPI devolvió 403 en esta sesión), así
que este script ejercita el pipeline real (clasificación, extracción,
chunking, embeddings, búsqueda) usando sqlite3 de la librería estándar en
vez de Postgres, y el HashingEmbedder de respaldo en vez del modelo de
sentence-transformers (que también requiere descargar pesos por internet).

Esto NO reemplaza probar la app real (FastAPI + Postgres + Docker) en tu
máquina — eso se hace con `docker-compose up` según el README. Este script
demuestra que la lógica de negocio (los módulos que si corren en este
sandbox) funciona correctamente sobre tus documentos reales.
"""
import glob
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from app.chunking import chunk_units
from app.classification import classify_filename
from app.embeddings import HashingEmbedder
from app.extraction import extract
from app.vectorstore import top_k_cosine

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_documents")

FOLDER_HINTS = {
    "PLANTILLA DE MEDICIONES SCI 3 7MAR24  TG V5 para cta.xlsx": "04.CUENTAS/CUENTA # 1",
    "F14 Plan de proyecto v04 APROBADO.xlsx": "08-PLAN DE PROYECTO",
    "FACTURA 982-ACCIONA CONSTRUCCION, S.A. - CUENTA 1.pdf": "04.CUENTAS/CUENTA # 1",
    "Infome de cuenta #10.docx": "04.CUENTAS/CUENTA # 10",
    "NOTA ACC-HDN-TEC-1098-2025.pdf": "06.NOTAS",
    "F27-Entrega Planos Hospital del Niño 22-03-2024.pdf": "02.DISEÑO/Acta de entrega",
}


def main():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE documents (id INTEGER PRIMARY KEY, filename TEXT, doc_type TEXT, "
        "doc_code TEXT, discipline TEXT, level_zone TEXT, confidence REAL)"
    )
    conn.execute(
        "CREATE TABLE chunks (id INTEGER PRIMARY KEY, document_id INTEGER, text TEXT, "
        "source_ref TEXT, embedding BLOB)"
    )

    embedder = HashingEmbedder(dim=384)
    all_vectors = []
    chunk_meta = []  # (document_id, filename, doc_type, doc_code, text, source_ref)

    print(f"{'='*100}\nFASE 0 — PRUEBA DE INTEGRACIÓN SOBRE DOCUMENTOS REALES DEL PILOTO\n{'='*100}\n")

    for path in sorted(glob.glob(os.path.join(SAMPLE_DIR, "*"))):
        filename = os.path.basename(path)
        ext = os.path.splitext(path)[1]
        folder_hint = FOLDER_HINTS.get(filename)

        classification = classify_filename(filename, folder_hint)
        units = extract(path, ext)
        chunks = chunk_units(units)

        cur = conn.execute(
            "INSERT INTO documents (filename, doc_type, doc_code, discipline, level_zone, confidence) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                filename,
                classification.doc_type.value,
                classification.doc_code,
                classification.discipline,
                classification.level_zone,
                classification.confidence,
            ),
        )
        doc_id = cur.lastrowid

        print(f"· {filename}")
        print(
            f"    clasificación: {classification.doc_type.value}"
            f"{' [' + classification.doc_code + ']' if classification.doc_code else ''}"
            f"  disciplina={classification.discipline or '—'}  zona={classification.level_zone or '—'}"
            f"  confianza={classification.confidence:.2f}"
        )
        print(f"    extracción: {len(units)} unidades -> {len(chunks)} fragmentos indexables")

        if chunks:
            vectors = embedder.embed([c.text for c in chunks])
            for c, vec in zip(chunks, vectors):
                conn.execute(
                    "INSERT INTO chunks (document_id, text, source_ref, embedding) VALUES (?, ?, ?, ?)",
                    (doc_id, c.text, str(c.source_ref), vec.tobytes()),
                )
                all_vectors.append(vec)
                chunk_meta.append(
                    (doc_id, filename, classification.doc_type.value, classification.doc_code, c.text, c.source_ref)
                )
        conn.commit()
        print()

    total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"{'='*100}\nTotal indexado: {total_docs} documentos, {total_chunks} fragmentos buscables\n{'='*100}\n")

    matrix = np.array(all_vectors, dtype=np.float32) if all_vectors else np.zeros((0, 384))

    queries = ["rociadores nivel 100", "factura acciona", "reunión subcontratista", "cuenta de avance"]
    for q in queries:
        print(f"--- búsqueda: {q!r} ---")
        qvec = embedder.embed([q])[0]
        top = top_k_cosine(qvec, matrix, k=3)
        if not top:
            print("   (sin resultados)")
        for idx, score in top:
            doc_id, filename, doc_type, doc_code, text, source_ref = chunk_meta[idx]
            print(f"   [{score:.3f}] {filename} ({doc_type}) — fuente={source_ref}")
            print(f"          {text[:100]!r}")
        print()

    assert total_docs == 6, f"esperaba 6 documentos, hay {total_docs}"
    assert total_chunks > 0, "no se generó ningún fragmento indexable"
    print("OK — pipeline de clasificación + extracción + chunking + embeddings + búsqueda funciona end-to-end.")


if __name__ == "__main__":
    main()
