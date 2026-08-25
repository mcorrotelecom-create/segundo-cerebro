"""Proveedor de embeddings — capa de recuperación local y gratuita (§03).

`SentenceTransformerEmbedder` es la implementación de calidad completa: un
modelo multilingüe de código abierto corriendo en CPU, sin costo por
documento y sin salir a internet después de la primera descarga del modelo.
Es "opcional" a propósito: pesa varios cientos de MB (modelo + PyTorch) y
no se instala por defecto (ver requirements.txt) porque no cabe en el plan
gratis de Render (512MB de RAM). Se instala aparte solo donde sobra RAM
(PC local, o un plan de Render con más memoria) — ver
requirements-semantic.txt.

`HashingEmbedder` es el respaldo — y, en el despliegue en la nube por
defecto, la opción real — sin dependencias ni descargas: un vectorizador
bag-of-words con feature hashing. No tiene la calidad semántica de un
modelo entrenado (no reconoce sinónimos ni paráfrasis), pero es liviano y
la búsqueda por palabras/texto completo (que `hybrid_search` combina con
esto) sigue funcionando igual de bien. Si `sentence-transformers` no está
instalado, o si su carga falla por cualquier motivo recuperable, el
pipeline cae a este respaldo automáticamente y deja constancia en el log —
nunca falla la ingesta completa por esto. (Aviso honesto: si el proceso
muere por quedarse sin RAM al intentar cargar el modelo pesado, eso lo mata
el sistema operativo antes de que este código pueda reaccionar — por eso el
modelo pesado no se instala donde la RAM es insuficiente, en vez de confiar
en que el `except` de abajo lo resuelva.)
"""
import hashlib
import logging
import re
from typing import Protocol

import numpy as np

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


class EmbeddingProvider(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> np.ndarray: ...


class HashingEmbedder:
    """Respaldo sin modelo: bag-of-words con feature hashing, normalizado."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            tokens = _TOKEN_RE.findall(text.lower())
            for tok in tokens:
                h = int(hashlib.blake2b(tok.encode("utf-8"), digest_size=4).hexdigest(), 16)
                vectors[i, h % self.dim] += 1.0
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm
        return vectors


class SentenceTransformerEmbedder:
    """Modelo local multilingüe (producción). Carga perezosa: el modelo solo
    se descarga/instancia la primera vez que se usa, no al importar el módulo.
    """

    def __init__(self, model_name: str, dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        self._ensure_loaded()
        return np.asarray(self._model.encode(texts, normalize_embeddings=True))


def get_embedder(model_name: str, dim: int) -> EmbeddingProvider:
    try:
        embedder = SentenceTransformerEmbedder(model_name, dim)
        embedder._ensure_loaded()
        return embedder
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de carga cae al respaldo
        logger.warning(
            "No se pudo cargar el modelo de embeddings '%s' (%s). "
            "Usando respaldo sin modelo (HashingEmbedder) — la búsqueda "
            "semántica pierde calidad hasta que el modelo esté disponible.",
            model_name,
            exc,
        )
        return HashingEmbedder(dim)
