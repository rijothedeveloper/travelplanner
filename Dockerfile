# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home \
       --shell /usr/sbin/nologin app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --no-cache \
    --python /usr/local/bin/python

COPY . .

USER 10001:10001
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]