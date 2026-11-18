# syntax=docker/dockerfile:1
# Frontend image: the built SPA behind nginx, which also proxies /api to the backend (one origin, no CORS).
# Build from the repo root: docker build -f apps/web-ts/Dockerfile .

ARG NODE_VERSION=24
ARG NGINX_VERSION=1.29

# ---- build: install only the web package and build the static files
FROM node:${NODE_VERSION}-alpine AS build
RUN corepack enable
WORKDIR /repo

# Manifests first for layer caching. pnpm needs every workspace manifest to check the lockfile.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web-ts/package.json apps/web-ts/
COPY architecture/site/package.json architecture/site/
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --filter web...

COPY apps/web-ts apps/web-ts
# The OpenAPI types are committed, so the build needs no Python.
RUN pnpm --filter web build

# ---- runtime: static files + reverse proxy
FROM nginx:${NGINX_VERSION}-alpine
# The official image renders /etc/nginx/templates/*.template with envsubst on start.
ENV API_UPSTREAM=http://api:8000 \
    PORT=80
COPY apps/web-ts/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /repo/apps/web-ts/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1:${PORT}/healthz || exit 1
