# wiz-control-app

Finds WiZ bulbs on the local network, shows their state, and changes brightness and color. Monorepo: Python server (uv workspace), Svelte + TypeScript frontend (pnpm), Docusaurus docs site.

## Layout

- `apps/` — runnable applications. `packages/` — shared libraries.
- Every folder there ends in `-py` (uv member) or `-ts` (pnpm package). A folder with no suffix belongs to neither workspace.
- `architecture/decisions/` — ADRs. `architecture/journal/` — the author's working journal.
- `architecture/site` — Docusaurus site that shows decisions and journal. Not an app.
- `.github/workflows/docs.yml` — deploys the site to GitHub Pages on push to `main`. `baseUrl` is `/wiz-control-app/`.

## Tooling

- mise pins python, uv, node, and pnpm in `mise.toml`. Nothing is installed globally, uv included.
- The root `pyproject.toml` is a virtual uv workspace root (`package = false`). It holds the shared dev tools.

## Rules

Repo-wide rules are in `.claude/rules/`: layout and layers, commits, journal, architecture docs.

- The journal is dictated by the author. Never write an entry or a finding on your own.
- WiZ discovery is UDP broadcast on the LAN, so the server must run on the bulbs' network segment.

## Commands

| Command | What it does |
| --- | --- |
| `mise install` | Install the pinned tools |
| `uv sync` | Install Python deps for every workspace member |
| `uv run pytest` | Run the tests (no real bulbs needed) |
| `pnpm install` | Install docs site deps |
| `pnpm dev:docs` | Run the docs site |
| `pnpm build:docs` | Build the docs site |
