FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

RUN apk add --no-cache \
    curl \
    bash

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system . && \
    uv pip install --system \
    "alembic==1.14.1" \
    "fastapi==0.115.6" \
    "uvicorn[standard]" \
    "asyncpg" \
    "sqlalchemy" \
    "pydantic"

COPY . .

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 5000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "5000", "--reload", "--proxy-headers", "--forwarded-allow-ips", "*"]