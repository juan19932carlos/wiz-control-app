# Repo layout

- Every runnable application lives in `apps/`. Libraries shared between apps live in `packages/`.
- Every folder in `apps/` and `packages/` ends in `-py` or `-ts`. The suffix decides which workspace owns it.
- `*-py` folders are uv workspace members, with their own `pyproject.toml`, `src/<module>/`, and `tests/`.
- `*-ts` folders are pnpm workspace packages, with their own `package.json`. Versions go in the pnpm `catalog:`.
- The Python import name drops the suffix: `packages/wiz-domain-py` is imported as `wiz_domain`.
- The frontend is Svelte + TypeScript + Vite. It talks to the Python server only over HTTP.
- Frontend styling is Tailwind CSS. UI components come from shadcn-svelte, copied into the app; do not add another component kit.
- The Docusaurus site is not an app. It lives in `architecture/site` and is a pnpm workspace package.
- Use uv for Python and pnpm for Node. Never pip, npm, or yarn at the repo root.
- Tools come from `mise.toml`. Run commands through `mise exec --` if the shell is not activated.

## Layers (Cosmic Python, `*-py` only)

- `domain/` holds the model: entities, value objects, domain events. It imports nothing from adapters, frameworks, or the network.
- `service_layer/` holds the use cases. It talks to the outside only through abstract ports (repositories, bulb gateways).
- `adapters/` implements the ports: the WiZ UDP client, repositories. Only adapters touch the network.
- `entrypoints/` holds the API and the CLI. They call the service layer, never the domain or adapters directly.

## Testing (TDD)

- Write the failing test first, then the code. No production code without a test that needed it.
- Domain and service layer tests use fakes and never open a socket.
- Adapter tests that need real bulbs are marked `integration` and are not part of the default run.
