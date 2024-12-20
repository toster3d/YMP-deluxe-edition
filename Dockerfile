FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

RUN mkdir -p src/instance && chmod -R 777 src/instance

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
    uv pip install --system .

COPY . .

RUN chown -R appuser:appuser src/instance

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1 

USER appuser

EXPOSE 5000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "5000", "--reload", "--proxy-headers", "--forwarded-allow-ips", "*"]