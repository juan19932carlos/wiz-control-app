# Architecture docs

- All docs are written in English.
- `architecture/decisions/` holds ADRs (Architecture Decision Records), named `NNNN-title.md`.
  - An ADR lists only lasting choices, with the rejected option and the reason.
  - A committed ADR is not edited. A new ADR supersedes the old one.
- `architecture/journal/` holds the journal. See `.claude/rules/journal.md`.
- `architecture/site/` is the Docusaurus site that shows `decisions/` and `journal/`. A new top-level section needs its own docs plugin instance in `architecture/site/docusaurus.config.ts`.
- The site homepage is the repo `README.md`. `architecture/site/src/pages/index.mdx` only imports it, so edit the README, not that file.
- Links in `README.md` use absolute URLs to the published site, because a relative link breaks either on GitHub or on the site.
