"""Configuración central de la aplicación.

Todo valor sensible o dependiente del entorno vive en variables de entorno
(ver .env.example en la raíz del proyecto). Nada de credenciales hardcodeadas.
"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/segundo_cerebro"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3_driver(cls, v: str) -> str:
        """Normaliza el prefijo de la cadena de conexión.

        Neon (y la mayoría de proveedores) entregan la cadena como
        "postgresql://..." (o, en algunos casos viejos, "postgres://...").
        Por defecto SQLAlchemy interpreta eso como "usa psycopg2", que no
        instalamos (usamos psycopg 3, más nuevo). En vez de exigirle al
        usuario editar la cadena a mano antes de pegarla — un paso manual
        más, y un error fácil de cometer — la normalizamos siempre aquí.
        """
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v

    # Claude API — se usa en Fase 1+ para extracción asistida, chat y agentes.
    # Fase 0 (ingesta, clasificación, búsqueda) no requiere esta clave.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    # Embeddings locales — corren en CPU, sin costo, sin salir a internet
    # después de la primera descarga del modelo. Solo se usa si
    # sentence-transformers está instalado (ver requirements-semantic.txt);
    # en el despliegue por defecto en la nube no lo está (no cabe en 512MB
    # de RAM), así que en la práctica se usa HashingEmbedder — ver
    # app/embeddings.py.
    embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # Ingesta
    max_upload_mb: int = 100
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 150
    # Dónde se guarda la copia de trabajo de cada documento subido desde la
    # interfaz. Ruta relativa a la carpeta desde la que se arranca el
    # backend (start_backend.bat ya se posiciona ahí) — funciona igual en
    # Windows, macOS o Linux, sin rutas absolutas de estilo Docker.
    originals_dir: str = "data/originals"

    # Nombre del proyecto por defecto para la Fase 0 (un solo proyecto piloto)
    default_project_code: str = "SHCI-HDN"
    default_project_name: str = "Sistema Contra Incendios — Hospital del Niño"

    # --- Despliegue en la nube (Render + Neon) ---
    # Orígenes permitidos para CORS. Solo importa si alguna vez corres
    # frontend y backend como dos servicios separados (ej. desarrollo local
    # sin Docker). En el despliegue combinado de un solo servicio (ver
    # Dockerfile en la raíz) frontend y backend son el mismo origen y esto
    # no entra en juego.
    cors_origins: str = "http://localhost:3000"

    # Traba mínima para que la aplicación no quede abierta a cualquiera en
    # internet una vez tiene una URL pública: un login HTTP básico (el
    # cuadro de usuario/contraseña nativo del navegador). NO es un sistema
    # de autenticación de verdad (eso es Fase 1+, con el esquema de roles
    # ya previsto en el modelo de datos) — es una sola cuenta compartida.
    # Si cualquiera de los dos queda vacío, no se exige nada — así el
    # desarrollo local sigue sin fricción.
    basic_auth_user: str | None = None
    basic_auth_password: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
