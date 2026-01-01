FROM ghcr.io/astral-sh/uv:latest AS uv_setup

FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxrender1 libxext6 libfontconfig1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv_setup /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

CMD ["python", "api/manage.py", "runserver", "0.0.0.0:8000"]