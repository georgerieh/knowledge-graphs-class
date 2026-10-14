FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

WORKDIR /app
RUN uv sync 

CMD ["/app/.venv/bin/fastapi", "run", "app/main:app", "--port", "8000", "--host", "0.0.0.0"]