"""Convierte las unidades extraídas (por página / hoja+filas / párrafo) en
fragmentos de tamaño manejable para embeber e indexar.

Una unidad ya extraída (una página, un bloque de filas de Excel, una tabla)
casi siempre es un tamaño razonable de por sí. Esta función solo divide más
las unidades que son demasiado largas para un solo embedding útil, y
preserva la referencia de fuente de la unidad original en cada fragmento
resultante — nunca se pierde la cita por trocear el texto.
"""
from dataclasses import dataclass
from typing import Any

from app.extraction import ExtractedUnit


@dataclass
class Chunk:
    text: str
    source_ref: dict[str, Any]


def chunk_units(
    units: list[ExtractedUnit], chunk_size: int = 1200, overlap: int = 150
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for unit in units:
        text = unit.text.strip()
        if not text:
            continue
        if len(text) <= chunk_size:
            chunks.append(Chunk(text=text, source_ref=unit.source_ref))
            continue

        start = 0
        part = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            piece = text[start:end].strip()
            if piece:
                ref = {**unit.source_ref, "part": part}
                chunks.append(Chunk(text=piece, source_ref=ref))
                part += 1
            if end == len(text):
                break
            start = end - overlap
    return chunks
