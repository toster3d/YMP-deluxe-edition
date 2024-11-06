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

ENV FLASK_APP=src.app:app
ENV PYTHONPATH=/app

USER appuser

EXPOSE 5000

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]