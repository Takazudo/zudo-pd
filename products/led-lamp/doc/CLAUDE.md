# Doc

Documentation site built with [zudo-doc](https://github.com/zudolab/zudo-doc) 9 — a zfb-based documentation framework with MDX, zfb's zudo-wind styling layer and zudo-react islands. Component evidence pages come from the published [`@takazudo/zudo-circuit-doc`](https://github.com/Takazudo/zudo-circuit-doc) runtime, configured by the repository-root `circuit.config.ts`. `doc/` is one package in the root pnpm workspace; install from the repository root.

## Tech Stack

- **zfb 5.2.2** (`@takazudo/zfb`, `-runtime`, `-md-wasm`, `-adapter-cloudflare`, exact pins) — build framework
- **@takazudo/zudo-doc 9.1.4** — layout, chrome, islands, default design tokens and doc routes; the Classic (`default`) theme pack is kept explicitly
- **@takazudo/zudo-circuit-doc 0.3.x** — evidence validation, component page generation, footprint/model previews, publication scans, browser smoke, and the MDX components/islands the generated pages use
- **MDX** — content format, authored under `src/content/`
- **Node 24** (`>=24 <25`), **pnpm 10.34.1** (root `packageManager`), **Python 3.12+** for the evidence validator and generator specs

## Commands

Run from `doc/` (each wraps the root config) or use the root scripts noted.

- `pnpm dev` — generates component pages, then runs the zfb dev server (port 4321), the doc-history server (port 4322) and the component watcher
- `pnpm dev:network` — same, but zfb binds `--host 0.0.0.0`; the doc-history server stays loopback-only and LAN clients reach it through zfb's `/doc-history/*` dev proxy
- **Trusted networks only:** this also serves your git doc-history — including UNPUBLISHED local commits — to anyone on the LAN via the `/doc-history/*` proxy
- `pnpm build` — the root build: enclosure viewer bundle, public models, component pages, then the zfb static export to `dist/` (`pnpm build:site` runs only the zfb step)
- `pnpm check` — zfb/TypeScript type checking of the host; `pnpm check:wind` — `zfb wind audit --fail-on error`
- `pnpm test:scripts` — tests for this host's own scripts (the zfb link-warning gate)
- `pnpm generate:components` / `pnpm check:components` — write / read-only check the generated pages and `circuit/generated/preflight.json` (`zudo-circuit-doc generate` / `check`; `check` also runs the validator and the model/footprint checks)
- `pnpm generate:footprint-previews` / `pnpm check:footprint-previews` — regenerate with the pinned KiCad 9.0.9 container / verify committed SVG previews without Docker
- `pnpm generate:models` / `pnpm check:models` — copy the reviewed selected WRL files into public preview assets / verify their bytes
- `pnpm generate:enclosure-viewer` / `pnpm check:enclosure-viewer` — bundle the standalone enclosure viewer / check the published print meshes
- `pnpm check:images`, `pnpm check:anchors`, `pnpm check:mermaid`, `pnpm check:built-component-references` — post-build image, strict anchor, Mermaid and component-reference checks
- `pnpm scan:artifacts` / `pnpm scan:doc-skill` — publication scan of the built site / of an isolated docs-to-agent corpus
- `pnpm test:model-viewer:browser` — `zudo-circuit-doc check-browser` with shell and search assertions (needs Chrome; set `CHROME_BIN` or pass a headless Chromium)
- `pnpm b4push` — runs the root `circuit/scripts/run-b4push.sh`: every credential-free gate except the browser smoke; it is not a deploy command

## Key Directories

```
../circuit.config.ts      # zudo-circuit-doc config (evidence, inventory provider, CAD, scan, browser smoke)
../circuit/
├── publication/          # selection.json, assets.json (public-file allowlist), integration-gloss.json
├── policy.json           # project validation gates run by `zudo-circuit-doc validate`
├── records/              # project-owned records the runtime does not read (document verification)
├── generated/preflight.json  # GENERATED publication report — regenerate, never hand-edit
└── scripts/run-b4push.sh
zfb.config.ts             # zudoDoc({ ...only fields you chose })
pages/
├── index.tsx             # 1-line re-export of the package home route
├── docs/[[...slug]].tsx  # scaffold doc-route stub + the zudo-circuit-doc islands seed import
└── lib/_circuit-doc-islands.ts  # imports @takazudo/zudo-circuit-doc/islands
public/assets/component-previews/
├── footprints/           # GENERATED, committed SVG previews + manifest
└── models/               # GENERATED, committed reviewed WRL previews
scripts/                  # scaffold link checker + this host's gates (link warnings, Mermaid, doc-skill scan)
src/
├── chrome-bindings.tsx   # registers circuitDocMdxExtras for generated pages
├── content/
│   └── docs/             # MDX content
│       └── components/   # GENERATED — never hand-edit; owned by zudo-circuit-doc
└── styles/global.css     # zudo-doc CSS chain + zudo-circuit-doc styles + token-override slot
enclosure-viewer/         # standalone esbuild/three.js enclosure viewer (not a zfb island)
```

**`src/content/docs/components/` is exclusively generated.** Edit the evidence under
`.claude/skills/` or the selection under `../circuit/publication/`, then run
`pnpm generate:components`. Generated pages keep the legacy
`# GENERATED by doc/component-docs` ownership marker on purpose (configured as
`docs.generatedMarker`); the package refuses to overwrite a marker-less file there.
The footprint SVGs, their manifest, and selected public WRLs are likewise generated
and committed: regenerate them from the reviewed canonical KiCad assets; never edit
them by hand. A component change must explicitly update the selection and its truthful
document kind before any generated page or preview can exist.

`pnpm b4push` completes every credential-free gate. CI runs its extra drift/link
checks and the browser smoke, and only then performs the credential-gated Cloudflare
preview deploy; missing credentials skip deployment, never validation.

Everything else — layout, header, sidebar, footer, doc chrome, islands, and the default design tokens — lives in `node_modules/@takazudo/zudo-doc`. For supported markup replacement, use `src/chrome-bindings.tsx` (`defineChromeBindings`) and the primary `Header` / `Footer` / `Sidebar` / `Toc` / `Breadcrumb` / `DocPager` slots or the named `headerRightComponents` registry. Keep the `mdxExtras: { ...circuitDocMdxExtras }` registration and the docs route's islands seed import. Settings you didn't set explicitly in `zfb.config.ts` use the package's documented defaults — hover `zudoDoc`'s `ZudoDocConfig` argument in your editor to see every field and its `@default`.

## Content Conventions

### Frontmatter

- Required: `title` (string)
- Optional: `description`, `sidebar_position` (number), `category`
- Sidebar order is driven by `sidebar_position`

### Admonitions

Available in all MDX files without imports, via directive syntax: `:::note`, `:::tip`, `:::info`, `:::warning`, `:::danger`, `:::caution`, `:::details`. Each accepts an optional **bracketed** title: `:::note[Custom Title]`.

Docusaurus-style `{title="..."}` is **NOT supported**. MDX parses the braces as a JS expression, so it either fails the build with `ReferenceError: title is not defined` or is silently ignored. Always use the bracketed form.

### Headings

Do NOT use h1 (`#`) in doc content — the page title from frontmatter is rendered as h1. Start content headings from h2 (`##`).

### Built-in MDX components

`@takazudo/zudo-doc` ships a few **globally-available MDX components** — usable in any `.mdx` file with **no import**. The seeded `getting-started/index.mdx` already uses one:

- `<CategoryNav category="..." />` — a card-grid list of the pages in a docs category (this is the one seeded into `getting-started/index.mdx`).
- `<CategoryTreeNav category="..." />` — the same listing as a compact nested tree, better for deeper hierarchies.
- `<SiteTreeNavDemo />` — a full-site documentation tree (the MDX-available wrapper of the `SiteTreeNav` island).

Admonitions (above), tabbed content (`<Tabs>` / `<TabItem>`, `<CodeGroup>`), and block math (`<MathBlock>`) work the same way — no import. Full reference: https://zudo-doc.takazudomodular.com/docs/components/

## Scaffold defaults and project extensions

The site follows create-zudo-doc 9.1.4 defaults, keeping the Classic (`default`) theme pack it used before zudo-doc 9 made Graphite the default.
See `SCAFFOLD.md` for the feature inventory, retained extensions, and sync procedure.

- **search** — package-owned full-text search and generated `search-index.json`
- **sidebarFilter**, **sidebarResizer**, **sidebarToggle** — built-in filtering and desktop sidebar controls
- **tocToggle** — show/hide the desktop table of contents
- **docHistory** — document edit history; generated component pages remain excluded
- **llmsTxt** — generates llms.txt for LLM consumption
- **imageEnlarge** — image enlargement
- **assetViewer** — viewer routes under `/files/` for public assets; index and search/LLM indexing retain the upstream off defaults
- **dynamicPageTransition** — client-side page navigation
- **footerCopyright** — the project's existing attribution

Intentional extensions include CJK handling, repo-root Claude resources, the body-foot
history strip, project navigation, Cloudflare adapter, the enclosure viewer, and the
zudo-circuit-doc integration (generated pages, previews and islands). Optional upstream
features stay off unless listed as an intentional extension; the design-token panel
(`designTokenPanel`, default off) is not mounted (#125). This is a single-locale site, so the header has
no language switcher.
