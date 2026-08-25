"""Punto de entrada de la API — Fase 0.

Endpoints disponibles en esta fase: subir documentos, listarlos, ver su
clasificación, y buscar sobre lo ya indexado con resultados citables.
Las cuentas de avance, el chat del proyecto y los agentes llegan en fases
posteriores, sobre esta misma base.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.main_state import init_embedder
from app.routers import documents, health, search
from app.security import BasicAuthMiddleware

logging.basicConfig(level=logging.INFO)

# El Dockerfile de la raíz construye el frontend (Next.js, export estático)
# y lo copia aquí — así un solo servicio de Render sirve la interfaz y la
# API juntas, sin necesitar un segundo servicio ni una URL separada.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(get_settings().originals_dir, exist_ok=True)
    init_db()
    init_embedder()
    yield


app = FastAPI(title="Segundo Cerebro de Ingeniería — API", version="0.1.0", lifespan=lifespan)

# Orden importa: Starlette hace que el último middleware agregado sea el
# más externo. CORS va al final para que incluso una respuesta 401 del
# BasicAuthMiddleware salga con los encabezados CORS correctos — si no, el
# navegador reporta "bloqueado por CORS" en vez del 401 real.
app.add_middleware(BasicAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)

# Se monta al final y a "/" a propósito: las rutas de la API de arriba ya
# quedaron registradas, así que siempre tienen prioridad sobre esto. Si no
# existe app/static todavía (ej. corriendo el backend solo, en desarrollo
# local sin el frontend construido), simplemente no se monta nada — la API
# sigue funcionando igual, solo no hay interfaz servida desde aquí.
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
