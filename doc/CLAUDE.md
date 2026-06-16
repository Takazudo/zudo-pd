# CLAUDE.md - Documentation Guidelines

This file provides guidance to Claude Code when working with documentation in this directory.

This is a **zudo-doc** site — a zfb / MDX / Tailwind / Preact static-site
framework (consuming `@takazudo/zfb` + `@takazudo/zdtp`). It replaced the
previous Docusaurus site. Output is a static `dist/` (plus `dist/_worker.js`)
deployed to **Cloudflare Workers**.

## Deployment

- **Host**: Cloudflare Workers (static assets) via the zfb Cloudflare adapter
  (`@takazudo/zfb-adapter-cloudflare`), which emits `dist/_worker.js`.
- **Base path**: `base = "/"` — the site is served at the domain root (NO
  `/pj/zudo-pd/` prefix anymore). Docs route under `/docs/...`.
- **Workflow**: `.github/workflows/main-deploy.yml` — on push to `main` it
  builds + typechecks, then deploys via `wrangler deploy --env production`.
  The deploy is **guarded**: it is skipped (build still runs, stays green)
  until both Cloudflare secrets are set AND the `wrangler.toml` domain
  placeholder is replaced (see the go-live checklist at the bottom).
- **Config**: `doc/wrangler.toml` (Workers static-assets shape) and
  `doc/zfb.config.ts` (collections, adapter, features).

## Local Development

```bash
pnpm dev        # dev server at http://localhost:4321
pnpm build      # production build → dist/ (incl. dist/_worker.js)
pnpm preview    # preview the built dist/
pnpm check      # TypeScript typecheck
```

### URL Reference Guidelines

When the user provides a local docs URL like `http://localhost:4321/docs/...`:

- **DO NOT fetch the URL** — it is the local zudo-doc dev server.
- **Instead, read the corresponding source file** under
  `doc/src/content/docs/`. Map URL → file (base is `/`, docs route prefix is
  `/docs/`):
  - `http://localhost:4321/docs/inbox/current-status` → `doc/src/content/docs/inbox/current-status.md`
  - `http://localhost:4321/docs/overview/circuit-diagrams` → `doc/src/content/docs/overview/circuit-diagrams.mdx`
- Use the Read tool on the actual `.md`/`.mdx` source.

## Directory Structure

- `src/content/docs/` — **the documentation pages** (this is the content root):
  - `overview/` — project overview, circuit diagrams, BOM
  - `components/` — individual component specifications
  - `learning/` — circuit design learning notes
  - `how-to/` — KiCad workflow, parts download, SVG export guides
  - `misc/` — footprint preview, misc
  - `inbox/` — status, debug logs, quick reference
- `public/` — **static assets, served at the site root**:
  - `circuits/` → `/circuits/<name>.svg` (circuit diagram SVGs)
  - `footprints/` → `/footprints/<name>.svg` (footprint layout SVGs)
  - `footprint-imgs/` → `/footprint-imgs/<name>.png` (footprint preview PNGs)
  - `datasheets/` (PDF), `img/`, `kicad/`, `favicon.ico`
- `src/config/settings.ts` — site name, nav, features, schemes
- `pages/`, `src/components/`, `plugins/` — framework internals (do NOT
  hand-edit; they come from the zudo-doc scaffold)
- `zfb.config.ts`, `wrangler.toml` — build + deploy config

## Authoring Rules (Markdown / MDX)

1. **File extension**: use `.md` when the page has no JSX; use `.mdx` only when
   it uses JSX components (`<Details>`, `<CategoryNav>`, etc.). Native `:::`
   admonitions do NOT require `.mdx`.
2. **Frontmatter**: `title:` is **required** (it renders as the page h1).
   `sidebar_position:` controls sidebar order (lower = higher). Optional
   `sidebar_label:`, `description:`.
3. **No `# H1` in the body** — start headings at `##` (the frontmatter `title`
   is the h1).
4. **Admonitions** — use the native directive syntax (globally available, no
   import):
   ```mdx
   :::note
   General information.
   :::

   :::tip[Custom Title]
   A helpful suggestion.
   :::
   ```
   Available: `:::note`, `:::tip`, `:::info`, `:::warning`, `:::danger`
   (and `:::caution`). Five core styles.
5. **Collapsible blocks** — use `<Details title="...">...</Details>` (global,
   no import). Makes the file `.mdx`.
6. **Category landing pages** — use `<CategoryNav category="<section>" />` in a
   section `index.mdx` (global, no import) to render a card grid of child pages.
7. **Images / diagrams** — reference assets from `public/` by root-absolute
   path: circuit SVGs `![alt](/circuits/<name>.svg)`, footprint SVGs
   `![alt](/footprints/<name>.svg)`, footprint PNGs
   `![alt](/footprint-imgs/<name>.png)`. **Each image must be a standalone
   markdown image paragraph** (its own line — not inside a link, table, or JSX
   wrapper) so the **image-enlarge** (click-to-zoom) feature activates.
   There is NO `<CircuitSvg>` / `<FootprintSvg>` component anymore — drop the
   SVG into `public/` and reference it as a plain markdown image.
8. **Mermaid** — keep fenced ` ```mermaid ` blocks; they render as diagrams.
9. **Internal links** — include the `.md`/`.mdx` extension matching the target
   file, e.g. `[BOM](../overview/bom.md)`, `[LM2596S](../components/lm2596s-adj.mdx)`.
   No `/pj/zudo-pd/` base prefix.
10. **Sidebar / nav** — there is NO `sidebars.js`. Sidebar order comes from each
    page's `sidebar_position` frontmatter; the 6 header tabs are configured in
    `src/config/settings.ts` (`headerNav`). To add a page, just create the file
    with a `title` + `sidebar_position`.

## MDX Syntax Rules

**CRITICAL**: MDX (Markdown + JSX) requires escaping certain characters in prose.

### Less-than / Greater-than (`<` and `>`)

MDX interprets `<` as the start of a JSX tag. In regular prose, escape them:

- **WRONG**: `Float or pull low (<0.8V) = Enable`
- **CORRECT**: `Float or pull low (&lt;0.8V) = Enable` — or wrap in code: `` `<0.8V` ``

### Curly Braces (`{` and `}`)

MDX interprets `{...}` as a JavaScript expression. Escape or use code:

- **WRONG**: `Use the formula {VIN - VOUT}`
- **CORRECT**: `Use the formula \`{VIN - VOUT}\``

### Escaping Table

| Character | Entity / fix          | When to escape                         |
| --------- | --------------------- | -------------------------------------- |
| `<`       | `&lt;` or backticks   | Always in prose (not in code blocks)   |
| `>`       | `&gt;` or backticks   | Always in prose (not in code blocks)   |
| `{` `}`   | backticks / `&#123;`  | When not JSX/MDX syntax                |

**Safe zones (no escaping):** inside fenced code blocks, inline code, and HTML
comments. After editing, run `pnpm build` — MDX compile errors fail the build
and name the offending file:line.

## Circuit Diagram Writing Rules

When creating or updating circuit diagrams in the documentation:

### 1. Use ASCII Art in Code Blocks

Illustrate circuits with ASCII art inside fenced code blocks:

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

### 2. Always Include a Full Connection List

Under every diagram, list components (U1, R1, C1...), pin numbers/names,
connection destinations, and signal/voltage levels.

### 3. ASCII Art Golden Rules

- **NEVER cross lines** unless they form an electrical junction.
- **NEVER route a line over a text label** — it reads as a connection. Route
  around, remove intermediate labels, or use `─→ Label` notation for distant
  connections.
- Use box-drawing chars: `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴`; arrows `→ ←`.
- **Avoid `┼`** unless it is a true 4-way junction.
- Draw shunt elements (e.g. output caps) as vertical drops to GND so they read
  as parallel, not series.
- Keep vertical bars `│` in the same character column (monospace alignment).
- Label all voltage levels and current ratings.

### 4. Generating Circuit / Footprint SVGs

- Circuit diagrams are generated with schemdraw — Python sources live in
  `/diagram-sources/*.py` at the repo root. Output SVGs go into
  `doc/public/circuits/` and are referenced as `![alt](/circuits/<name>.svg)`.
- Footprint SVGs are exported from KiCad (`kicad-cli fp export svg ...`) into
  `doc/public/footprints/` and referenced as `![alt](/footprints/<name>.svg)`.
- See `how-to/create-circuit-svg.mdx` and `how-to/create-footprint-svg.mdx` for
  the full workflows.

## Documentation Language

All documentation must be written in **English** (content, diagrams, labels,
commit messages) for international accessibility.

## Cloudflare Deploy (live)

Go-live is complete — pushes to `main` build **and publish** the site to
Cloudflare Workers static assets at **https://pd.takazudomodular.com**.

What is wired up:

1. **GitHub Actions secrets** (repo Settings → Secrets and variables → Actions):
   - `CLOUDFLARE_API_TOKEN` — token with **Workers: Edit** permission
   - `CLOUDFLARE_ACCOUNT_ID` — the Cloudflare account id
2. **Docs subdomain** is set in `doc/wrangler.toml`
   (`[[env.production.routes]]` → `pattern = "pd.takazudomodular.com"`). The apex
   `takazudomodular.com` is the main site, so docs live on the `pd.` subdomain.
   `siteUrl` in `src/config/settings.ts` is kept in sync.
3. **Custom domain** — `custom_domain = true` makes wrangler provision the
   Workers custom domain + DNS record automatically (the `takazudomodular.com`
   zone must be on the same Cloudflare account as `CLOUDFLARE_ACCOUNT_ID`).

The deploy job in `.github/workflows/main-deploy.yml` still self-guards: it skips
the publish (build-only) if either secret is missing or `wrangler.toml` is
reverted to the placeholder token, so `main` stays green either way.
