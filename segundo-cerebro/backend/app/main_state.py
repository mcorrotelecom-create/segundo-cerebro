"""Estado compartido de la aplicación (el modelo de embeddings se carga una
sola vez al arrancar, no en cada request).
"""
from app.config import get_settings
from app.embeddings import EmbeddingProvider, get_embedder as _load_embedder

_embedder: EmbeddingProvider | None = None


def init_embedder() -> None:
    global _embedder
    settings = get_settings()
    _embedder = _load_embedder(settings.embedding_model_name, settings.embedding_dim)


def get_embedder() -> EmbeddingProvider:
    if _embedder is None:
        init_embedder()
    return _embedder
