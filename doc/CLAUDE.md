# zudo-pd Documentation

Documentation site for the zudo-pd USB-PD modular synthesizer power supply project, built with the zudo-doc framework.

## Tech Stack

- **Astro 6** — static site generator with Content Collections
- **MDX** — via `@astrojs/mdx`, content in `src/content/docs`
- **Tailwind CSS v4** — via `@tailwindcss/vite` (not `@astrojs/tailwind`)
- **Preact** — for interactive islands only (TOC scroll spy, sidebar toggle, collapsible categories), with compat mode for React API compatibility
- **Shiki** — built-in code highlighting, dual theme (light/dark)
- **TypeScript** — strict mode via `astro/tsconfigs/strict`

## Commands

- `pnpm dev` — Astro dev server (port 3800)
- `pnpm dev:network` — dev server with `--host 0.0.0.0` for LAN access
- `pnpm build` — static HTML export to `dist/`
- `pnpm check` — Astro type checking
- `pnpm b4push` — pre-push validation: format check -> typecheck -> build

## Deployment

- **Production URL**: https://takazudomodular.com/pj/zudo-pd/
- **Base Path**: `/pj/zudo-pd/`
- **Deployment**: Automatic on push to `main` via Netlify

## Key Directories

```
src/
├── components/          # Astro + Preact components
│   └── admonitions/     # Note, Tip, Info, Warning, Danger
├── config/              # Settings, color schemes, sidebars, i18n
├── content/
│   └── docs/            # MDX content
├── hooks/               # Preact hooks (scroll spy)
├── integrations/        # Search index, Claude Resources
├── layouts/             # doc-layout.astro
├── pages/               # File-based routing
│   └── docs/[...slug]   # Doc routes
├── plugins/             # Inlined remark/rehype plugins
├── styles/
│   └── global.css       # Design tokens (@theme) & Tailwind config
├── types/               # TypeScript type definitions
└── utils/               # Utility functions (nav, sidebar, slug, base)
```

## Conventions

### Components: Astro vs Preact

- Default to **Astro components** (`.astro`) — zero JS, server-rendered
- Use **Preact islands** (`client:load`) only when client-side interactivity is needed
- Preact runs in compat mode, so components can use React-style imports and APIs
- Current Preact islands: `toc.tsx`, `mobile-toc.tsx`, `sidebar-toggle.tsx`, `sidebar-tree.tsx`, `theme-toggle.tsx`, `site-tree-nav.tsx`

### Content Collections

- Schema defined in `src/content.config.ts` (Zod validation)
- Uses Astro 6 `glob()` loader with `src/content/docs` base directory
- Required frontmatter: `title` (string)
- Optional: `description`, `sidebar_position` (number), `category`
- Sidebar order is driven by `sidebar_position`

### Admonitions

Available in all MDX files without imports (registered globally in doc page):
`<Note>`, `<Tip>`, `<Info>`, `<Warning>`, `<Danger>` — each accepts optional `title` prop.

### Enabled Features

- **search** — client-side MiniSearch with search-index.json
- **sidebarFilter** — filter input in sidebar tree
- **claudeResources** — auto-generates docs from .claude/ directory
- **sidebarResizer** — draggable sidebar width
- **mermaid** — Mermaid diagram rendering
- **colorMode** — light/dark theme toggle

### Disabled Features

i18n, versioning, math/KaTeX, docHistory, aiAssistant, colorTweakPanel, sidebarToggle, llmsTxt, docMetainfo, docTags, htmlPreview

## URL Reference Guidelines

When the user provides URLs starting with `http://localhost:3800/pj/zudo-pd/`:

- **DO NOT fetch the URL** — these are local documentation URLs
- **Instead, find and read the corresponding markdown file** in `src/content/docs/`
- Map URLs to file paths: `/pj/zudo-pd/docs/inbox/overview` -> `src/content/docs/inbox/overview.md`

## Design Tokens & CSS

The design token system uses a three-tier color strategy defined in `src/styles/global.css`:
1. **Palette** (p0-p15) — raw color values
2. **Semantic** — purpose-driven tokens (--color-fg, --color-bg, etc.)
3. **Component** — Tailwind utilities (text-fg, bg-surface, border-muted, etc.)

Spacing uses `hsp-*` (horizontal) and `vsp-*` (vertical) tokens.
