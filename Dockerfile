# Single-container deploy for free hosts (Render / Hugging Face Spaces / Cloud Run / Koyeb).
# FastAPI serves BOTH the REST API and the static dashboard (same-origin),
# so no nginx/proxy is needed. The CROO CAP provider (Node) is a separate,
# optional process started only when real CROO credentials exist.
FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Install the API package
COPY api/pyproject.toml ./api/pyproject.toml
COPY api/app ./api/app
RUN pip install --no-cache-dir -e ./api

# Static dashboard served by FastAPI at "/"
COPY frontend ./frontend

# Job artifacts
RUN mkdir -p /app/runs
ENV RUNS_DIR=/app/runs \
    FRONTEND_DIR=/app/frontend \
    PYTHONUNBUFFERED=1

# Most free hosts inject $PORT; default to 8000 locally.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --app-dir api --host 0.0.0.0 --port ${PORT:-8000}"]
