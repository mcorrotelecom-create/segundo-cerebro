"""Búsqueda por similitud de coseno en memoria (ver nota de diseño en
app/models.py — no se usa pgvector a propósito, a esta escala no hace falta).
"""
import numpy as np


def top_k_cosine(query: np.ndarray, matrix: np.ndarray, k: int) -> list[tuple[int, float]]:
    """Devuelve los índices (posición dentro de `matrix`) de los k vectores
    más similares a `query`, junto con su score de coseno, ordenados de
    mayor a menor similitud.

    Asume que `query` y las filas de `matrix` ya están normalizadas a norma
    1 (ambos proveedores de embeddings lo garantizan), así que la similitud
    de coseno es simplemente el producto punto.
    """
    if matrix.size == 0:
        return []
    scores = matrix @ query
    k = min(k, len(scores))
    top_idx = np.argpartition(-scores, k - 1)[:k]
    top_idx = top_idx[np.argsort(-scores[top_idx])]
    return [(int(i), float(scores[i])) for i in top_idx]
