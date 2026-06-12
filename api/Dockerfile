FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir -e .
RUN mkdir -p /app/runs
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
