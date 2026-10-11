FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

# ------- deps stage -------
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------- runtime stage -------
FROM deps AS runtime

COPY . .

RUN set -eu; \
    test -f app/version.py; \
    test -f app/api/v1/routes/health.py; \
    grep -q '@router.get("/version")' app/api/v1/routes/health.py; \
    grep -q 'app.include_router(api_router, prefix="/api/v1")' app/main.py; \
    grep -q 'app.include_router(health.router)' app/main.py

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}"]
