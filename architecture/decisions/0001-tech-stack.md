# 0001. Tech stack

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

An app that finds WiZ bulbs on the local network, shows their current state, and changes them: brightness up, brightness down, color.

It is also a learning project for TDD and DDD as described in *Architecture Patterns with Python* (Cosmic Python). Python is preferred everywhere it is reasonable. The frontend is the exception: it is TypeScript.

Only lasting choices are listed. This is a snapshot. When a choice changes, a new ADR supersedes the row. This file is not edited after it is committed.

## Decision

| Area | Choice | Rejected | Why |
| --- | --- | --- | --- |
| Language | Python 3.14 for domain and server, TypeScript for the frontend | Python for the frontend too | Python is the author's preference. The browser needs JS, and a typed TS SPA beats a Python wrapper over a JS UI. |
| Tool versions | mise | Global installs, pyenv, asdf | One file pins python, uv, node, and pnpm. Nothing is installed globally. |
| Python packages and monorepo | uv workspace over `apps/*-py` and `packages/*-py` | Poetry, pip + venv, one repo per app | One lockfile for every Python member. Shared code is a workspace package, not a copy. |
| Architecture | DDD with Cosmic Python layers: domain, service layer, adapters, entrypoints | Framework-centric code (logic in route handlers) | The bulb model must not depend on the WiZ UDP protocol or the web framework, so both can be swapped and the domain is tested without a network. |
| Web framework (server) | FastAPI | Flask, Django | Async, like the UDP calls to the bulbs. Generates the OpenAPI schema the frontend consumes. Pydantic models at the API edge only. |
| Persistence | None. Discovered bulbs live in an in-memory repository | SQLite, PostgreSQL | The bulbs are the source of truth for their own state. Rediscovery on start is cheap. The repository port stays, so a database can be added later behind it. |
| Testing | TDD with pytest. Unit tests on the domain and service layer with fakes; integration tests on adapters | Tests written after the code | Matches the Cosmic Python test pyramid. Fakes make the domain testable without real bulbs. |
| Frontend | Svelte with TypeScript, built with Vite, managed with pnpm | NiceGUI, FastAPI + Jinja + HTMX, a separate repo for the frontend | Standard SPA with a clean split: the server owns the API, the client only calls it over HTTP. Node and pnpm are already in the repo for Docusaurus, so the cost is small. NiceGUI ties the UI to the Python process. HTMX means HTML and CSS by hand. A separate repo loses API and client changes in one commit. |
| WiZ protocol client | Own async UDP client in `packages/wiz-protocol-py` | `pywizlight` | The protocol is small: JSON over UDP port 38899. Owning it teaches the protocol and keeps the adapter thin and testable. |
| Code quality | ruff and pyright for Python. prettier, eslint, and svelte-check for TypeScript | black + flake8 + mypy | ruff replaces several Python tools at once. pyright is the checker most editors already run. |
| API contract | TypeScript types generated from the FastAPI OpenAPI schema with `openapi-typescript` | Hand-written TS types | One source of truth. A server change that breaks the client fails the frontend type check. |
| Live state in the UI | Polling from the frontend | Server-Sent Events, WebSockets | Simplest option that works. SSE can replace it later in a new ADR. |
| Frontend app shape | Svelte + Vite single-page app | SvelteKit | One screen, no routing or server-side rendering needed. |
| UI styling and components | Tailwind CSS + shadcn-svelte | Tailwind alone, Pico CSS, Skeleton | shadcn-svelte gives accessible slider, switch, and card components that are copied into the repo and owned by it. Tailwind alone means building every control by hand. Pico is classless and hard to customize. Skeleton has less adoption. |
| Naming of apps and packages | Folder suffix `-py` or `-ts` in `apps/` and `packages/` | Separate `apps-py/` and `apps-ts/` trees | uv and pnpm each pick their members by suffix glob, so neither tool sees the other's folders. The language is visible in the name. |

## Consequences

- The repo has two package managers: uv for `*-py` members, pnpm for `*-ts` members and the docs site.
- A folder without a `-py` or `-ts` suffix in `apps/` or `packages/` belongs to neither workspace.
- WiZ discovery uses UDP broadcast, so the server must run on the same network segment as the bulbs.
- Nothing survives a server restart. Custom names or rooms for bulbs would need persistence and a new ADR.
