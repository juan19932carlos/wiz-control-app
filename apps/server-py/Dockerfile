# syntax=docker/dockerfile:1
# Backend image. Build from the repo root: docker build -f apps/server-py/Dockerfile .

ARG PYTHON_VERSION=3.14
ARG UV_VERSION=0.13.9

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---- build: resolve and install only wiz-server and its workspace deps into /app/.venv
FROM python:${PYTHON_VERSION}-slim AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# Manifests first, so dependency layers are cached until a lockfile or pyproject changes.
COPY pyproject.toml uv.lock ./
COPY apps/server-py/pyproject.toml apps/server-py/
COPY packages/wiz-protocol-py/pyproject.toml packages/wiz-protocol-py/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package wiz-server --no-install-workspace

COPY apps/server-py apps/server-py
COPY packages/wiz-protocol-py packages/wiz-protocol-py
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package wiz-server --no-editable

# ---- runtime: the venv only, no uv, no sources, non-root
FROM python:${PYTHON_VERSION}-slim
RUN useradd --system --uid 10001 wiz
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    WIZ_HOST=0.0.0.0 \
    WIZ_PORT=8000
USER wiz
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD ["python", "-c", "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"WIZ_PORT\"]}/api/health', timeout=2)"]
CMD ["wiz-server"]
