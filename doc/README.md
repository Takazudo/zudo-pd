# USB-PD Modular Synth Power Documentation

This directory is the documentation site for the USB-PD powered modular
synthesizer power supply. It is a [zudo-doc](https://github.com/takazudo) site
(a zfb / MDX / Tailwind / Preact static-site framework) consuming
`@takazudo/zfb` + `@takazudo/zdtp`, deployed to **Cloudflare Workers** (static
assets).

## Setup

```bash
pnpm install        # install dependencies
pnpm dev            # start dev server at http://localhost:4321
pnpm build          # production build (emits dist/, incl. dist/_worker.js)
pnpm preview        # preview the built dist/ locally
pnpm check          # TypeScript typecheck
```

## Directory Structure

```
doc/
├── src/
│   ├── content/docs/   # Documentation content (the pages)
│   │   ├── overview/   # Project overview, circuit diagrams, BOM
│   │   ├── components/ # Individual component specifications
│   │   ├── learning/   # Circuit design learning notes
│   │   ├── how-to/     # How-to guides
│   │   ├── misc/       # Footprint preview, misc
│   │   └── inbox/      # Status, debug logs, quick reference
│   ├── config/         # settings.ts (site config, nav), schemas
│   ├── components/     # Framework Preact components (do not edit by hand)
│   └── ...
├── public/             # Static assets served at site root
│   ├── circuits/       # Circuit diagram SVGs   → /circuits/<name>.svg
│   ├── footprints/     # Footprint layout SVGs  → /footprints/<name>.svg
│   ├── footprint-imgs/ # Footprint preview PNGs → /footprint-imgs/<name>.png
│   ├── datasheets/     # Component datasheets (PDF)
│   ├── img/            # General images
│   └── kicad/          # KiCad screenshots
├── pages/              # zfb route files (framework — do not edit by hand)
├── plugins/            # zfb build plugins (search, doc-history, public copy)
├── zfb.config.ts       # zfb build config (collections, adapter, features)
└── wrangler.toml       # Cloudflare Workers deploy config
```

## Adding Documentation

1. Create a `.md` (no JSX) or `.mdx` (with JSX) file in the appropriate
   `src/content/docs/<section>/` directory.
2. Add frontmatter — `title:` is required; `sidebar_position:` controls order:
   ```yaml
   ---
   title: My Page
   sidebar_position: 3
   ---
   ```
3. Write content in Markdown/MDX. Start headings at `##` (the `title` renders as
   the h1). See `CLAUDE.md` in this directory for the full authoring rules.

## Tech Stack

- **zudo-doc** / **zfb** (`@takazudo/zfb`) — static-site framework
- **Preact** — UI rendering (server-rendered, islands for interactivity)
- **MDX** — Markdown + JSX content
- **Tailwind CSS** — styling
- **Mermaid** — diagram rendering
- **TypeScript** — type safety
- **Cloudflare Workers** — hosting (static assets via the zfb CF adapter)

## Commands

- `pnpm dev` — dev server at http://localhost:4321
- `pnpm build` — production build → `dist/`
- `pnpm preview` — preview the built `dist/`
- `pnpm check` — TypeScript typecheck
- `pnpm check:html` — validate built HTML
