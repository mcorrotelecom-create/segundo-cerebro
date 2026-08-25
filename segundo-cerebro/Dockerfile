# Construye la interfaz (Next.js) y el backend (FastAPI) juntos en una
# sola imagen — un solo servicio para desplegar (en Render: "New Web
# Service" con Environment = Docker, Root Directory vacío/raíz del repo),
# en vez de dos servicios separados que hay que conectar a mano con URLs
# y CORS. Esto se construye en la nube (en el servidor de Render) — nunca
# corre Docker en tu computadora.

# ---- Etapa 1: construir la interfaz como archivos estáticos ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build
# El resultado queda en /frontend/out (por "output: export" en next.config.js)

# ---- Etapa 2: backend + la interfaz ya construida ----
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /frontend/out ./static

# El plan gratis de Render tiene disco efímero (se borra en cada reinicio/
# redeploy/"dormida") — por diseño, la app no depende de él para nada
# permanente: guarda un documento subido solo el tiempo que tarda en
# procesarlo (ver app/routers/documents.py) y borra la copia enseguida;
# lo que sí persiste de verdad (clasificación, texto extraído, fragmentos,
# embeddings) vive en Postgres (Neon), no en este disco.
RUN mkdir -p data/originals

EXPOSE 10000
# Render, para servicios Docker, espera por defecto que la aplicación
# escuche en el puerto 10000 — a menos que definas tú mismo la variable de
# entorno $PORT con otro valor. Por eso el respaldo aquí es 10000 y no un
# número inventado: así funciona sin agregar ninguna variable de entorno
# extra. Si corres esta imagen a mano en tu PC, sigue funcionando igual
# (usa 10000 salvo que definas $PORT).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
