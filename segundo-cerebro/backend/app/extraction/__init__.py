"""Extractores de texto por tipo de archivo.

Cada extractor devuelve una lista de `ExtractedUnit`: un fragmento de texto
más la referencia exacta a dónde vive dentro del documento original (página,
hoja+filas, párrafo). Esa referencia es lo que después se convierte en la
cita ("Fuente: ...") que exige la propuesta técnica (§04, §09).
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractedUnit:
    text: str
    source_ref: dict[str, Any]


def extract(file_path: str, file_ext: str) -> list[ExtractedUnit]:
    ext = file_ext.lower().lstrip(".")
    if ext == "pdf":
        from app.extraction.pdf_extractor import extract_pdf
        return extract_pdf(file_path)
    if ext in ("xlsx", "xlsm", "xls"):
        from app.extraction.excel_extractor import extract_excel
        return extract_excel(file_path)
    if ext == "docx":
        from app.extraction.docx_extractor import extract_docx
        return extract_docx(file_path)
    raise ValueError(f"Tipo de archivo no soportado para extracción: .{ext}")
