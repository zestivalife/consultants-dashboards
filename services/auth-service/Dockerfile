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
    test -f app/api/v1/routes/people_access.py; \
    test -f app/api/v1/routes/master_data.py; \
    test -f app/api/v1/router.py; \
    grep -q "people_access" app/api/v1/router.py; \
    grep -q "master_data" app/api/v1/router.py; \
    test ! -f app/api/v1/routes/identity.py; \
    test ! -f app/api/v1/routes/onboarding.py; \
    test ! -f app/core/otp.py; \
    test ! -f app/db/models/otp_verification.py; \
    ! grep -q 'include_router(.*identity' app/api/v1/router.py; \
    ! grep -q 'include_router(.*onboarding' app/api/v1/router.py; \
    ! grep -q 'verify-otp' app/api/v1/routes/auth.py; \
    ! grep -q 'resend-otp' app/api/v1/routes/auth.py; \
    ! grep -q 'forgot-password' app/api/v1/routes/auth.py

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
