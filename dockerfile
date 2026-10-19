FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    tar \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

WORKDIR /app

RUN uv sync --locked

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uv", "run", "python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]