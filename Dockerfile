FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[service]"

COPY rate_limiter/ ./rate_limiter/

CMD ["sh", "-c", "uvicorn rate_limiter.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]