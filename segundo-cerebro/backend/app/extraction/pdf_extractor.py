"""Extracción de texto y tablas de archivos PDF, página por página.

Usa pdfplumber porque preserva razonablemente el layout (importante para
tablas de cantidades) y es puro Python — sin dependencias de sistema como
poppler que compliquen el contenedor Docker.

Un PDF escaneado (sin capa de texto) produce texto vacío por página; ese
caso se marca explícitamente para que la ingesta no finja haber leído algo
que no leyó (ver principio de "nunca presentar una inferencia como un
hecho" de la propuesta técnica). El OCR sobre PDFs escaneados es una
extensión de Fase 2, no de Fase 0.

Nota de robustez encontrada probando con documentos reales del piloto: una
parte no trivial de los PDF de este proyecto (notas, actas firmadas y
escaneadas) tiene una estructura de páginas mal formada que pdfminer/
pdfplumber no logra leer directamente (reporta 0 páginas). `pikepdf` puede
reescribir casi cualquier PDF a una forma bien formada sin tocar su
contenido, así que se usa como reparación automática antes de reintentar.
"""
import contextlib
import os
import tempfile

import pikepdf

from app.extraction import ExtractedUnit


@contextlib.contextmanager
def _open_robust(file_path: str):
    """Abre el PDF con pdfplumber; si el PDF está mal formado y pdfplumber
    no encuentra páginas, lo repara con pikepdf (reescritura sin pérdida de
    contenido) y reintenta una vez sobre una copia temporal.
    """
    import pdfplumber

    pdf = pdfplumber.open(file_path)
    if len(pdf.pages) > 0:
        try:
            yield pdf
        finally:
            pdf.close()
        return

    pdf.close()
    fd, repaired_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        with pikepdf.open(file_path) as src:
            src.save(repaired_path)
        pdf = pdfplumber.open(repaired_path)
        try:
            yield pdf
        finally:
            pdf.close()
    finally:
        if os.path.exists(repaired_path):
            os.remove(repaired_path)


def extract_pdf(file_path: str) -> list[ExtractedUnit]:
    units: list[ExtractedUnit] = []
    with _open_robust(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                units.append(ExtractedUnit(text=text, source_ref={"page": page_index}))
            else:
                units.append(
                    ExtractedUnit(
                        text="",
                        source_ref={"page": page_index, "note": "sin_texto_extraible_posible_escaneo"},
                    )
                )

            tables = page.extract_tables() or []
            for t_index, table in enumerate(tables, start=1):
                rows_txt = "\n".join(
                    " | ".join(cell if cell else "" for cell in row) for row in table if row
                )
                if rows_txt.strip():
                    units.append(
                        ExtractedUnit(
                            text=rows_txt,
                            source_ref={"page": page_index, "table": t_index},
                        )
                    )
    return units
