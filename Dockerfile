# syntax=docker/dockerfile:1
# Single-instance image: build the Next.js static export, then serve it from
# FastAPI alongside the /api routes. One Railway service, same origin, no CORS.

# ---- stage 1: build the frontend static export ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
# output:'export' emits ./out (calls the API at same-origin /api).
RUN npm run build

# ---- stage 2: backend runtime that also serves the frontend ----
FROM python:3.12-slim AS backend
WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend /fe/out ./frontend_static

ENV FRONTEND_DIR=/app/frontend_static
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
# Railway injects $PORT; default to 8000 for local runs.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
