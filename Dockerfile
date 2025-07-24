FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . .

RUN uv sync --frozen

RUN mkdir -p /vol/web/static

COPY ./scripts/wait-for-it.sh /usr/local/bin/
COPY ./scripts/web.sh /docker/web.sh
COPY ./scripts/scheduler.sh /docker/scheduler.sh

RUN chmod +x /docker/web.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh \
    && chmod +x /docker/scheduler.sh