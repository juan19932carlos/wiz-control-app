# 0002. Documentation site

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

The ADRs and the journal are markdown files in `architecture/`. We want to read them as a site, with a sidebar, Mermaid diagrams, and a public page on GitHub Pages.

## Decision

| Area | Choice | Rejected | Why |
| --- | --- | --- | --- |
| Documentation site | Docusaurus | MkDocs (Python) | Same setup as the author's `aws-xray-example` repo, which already works. MkDocs would avoid Node but means learning a second docs tool. |

## Consequences

- The site lives in `architecture/site`. It reads `architecture/decisions` and `architecture/journal` in place, so the markdown has one source.
- Mermaid works through `@docusaurus/theme-mermaid`.
- A GitHub Actions workflow publishes it to GitHub Pages on every push to `main`.
- The repo needs Node and pnpm, pinned in `mise.toml`, even though the app is Python.
