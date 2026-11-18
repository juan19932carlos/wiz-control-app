# 0003. Containers and delivery

- **Status:** Accepted
- **Date:** 2026-11-18

## Context

The app has to run on a home server on the same LAN as the bulbs, and the code lives on GitHub. We want reproducible artifacts built by a pipeline, one stack to run locally or for tests, and one for production that uses the published artifacts.

The browser must reach the SPA and the API from the same origin, so CORS never comes up. The proxy that does it should be as light as possible.

## Decision

| Area | Choice | Rejected | Why |
| --- | --- | --- | --- |
| Packaging | One Docker image per app: `wiz-control-server` and `wiz-control-web` | systemd services on the host | Same artifact in CI, locally, and in production. Nothing to install on the host but Docker. |
| Reverse proxy | nginx inside the web image: serves the SPA and proxies `/api` to the API | A separate Caddy or Traefik container, CORS middleware in FastAPI, FastAPI serving the static files | No third container: the web image already needs a static server. One origin, so no CORS. FastAPI serving files would tie the frontend artifact to the backend. |
| Container network | Default compose bridge network. Only the web port is published | `network_mode: host` | Discovery sweeps the subnet with unicast, and the replies pass the bridge NAT. Verified with three real bulbs. Host mode would also expose the API to the LAN. |
| Registry | GitHub Container Registry (GHCR) | Docker Hub | Next to the code. CI pushes with the built-in `GITHUB_TOKEN`, no extra secret. |
| Pipeline | GitHub Actions with `jdx/mise-action` | One setup action per tool | CI gets the exact tool versions from `mise.toml`, the same as local. |
| Image tags | `latest` from `main`, `sha-<short>` on every push, `vX.Y.Z` and `vX.Y` from `v*` git tags | `latest` only | Production can pin a release with `WIZ_VERSION` and roll back. |
| Compose files | `compose.yaml` builds from the Dockerfiles. `compose.prod.yaml` pulls from GHCR | One file with profiles or overrides | Two short files, each readable alone. |

## Consequences

- Broadcast discovery does not work from the bridge network. `WIZ_TARGETS` must name the LAN subnet. Both compose files refuse to start without it.
- Docker builds use the repo root as context, because each app needs workspace files (`uv.lock`, `pnpm-lock.yaml`).
- The web image builds without Python, because the generated OpenAPI types are committed. CI fails if they drift from the server.
- There is no authentication. Anyone on the LAN who can open the web port can control the bulbs.
