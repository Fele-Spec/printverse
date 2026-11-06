FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PRINTVERSE_DB=/app/data/printverse.db

WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY backend ./backend
COPY configs ./configs
COPY manifests ./manifests
COPY frontend/public ./frontend/public
RUN mkdir -p /app/data /app/runtime /app/logs /app/database

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
