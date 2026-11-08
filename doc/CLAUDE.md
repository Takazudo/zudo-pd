# Documentation guidance

This is a zudo-doc site using zfb, MDX, zudo-wind CSS and zfb's zudo-react islands. Framework packages own
layout and chrome. `zfb.config.ts` owns the project configuration, using the `sumi`
theme. The route stubs under `pages/` stay package-shaped; custom preview components
are registered through `src/chrome-bindings.tsx`.

## Content ownership

- `project/`: current-state owner, project brief, evidence limits, current procedures and repository entry points.
- `architecture/`: P15 shared input, PD15 and PD20 designs, interfaces, component map and acceptance-gate owner.
- `research/`: orientation to existing research and exploratory records.
- `decisions/`: project decisions linked to their retained rationale.
- `verification/`: assembly, bring-up and test procedures with explicit evidence limits.
- `components/`: generated catalog, exact records and integration evidence; never hand-edit.
- `archive/`: guide to historical material. `overview/`, `inbox/`, `learning/` and
  `misc/` keep stable URLs and explicit historical banners.

Do not append new current-state corrections to historical narratives. Update the
current page and link it from the archive when useful. Preserve historical sources
and diagnostic records, including their evidence anchors.

The catalog is a reviewed projection of repo-root `.claude/skills/`. Its publication
matrix deliberately leaves raw skills unpublished (`claudeResources: false`). Read
[`circuit/ARCHITECTURE.md`](../circuit/ARCHITECTURE.md) before changing the projection.
The installed `@takazudo/zudo-circuit-doc` package owns the renderer and generated
component runtime; `circuit.config.ts` and `circuit/publication/` hold this project's
configuration and reviewed publication choices. Generated evidence already carries
source provenance, so generated-page git history is excluded from the history UI.

## Commands

```sh
pnpm dev                       # zfb :4321 + history :4322 + component watcher
pnpm --dir doc dev:zfb         # zfb alone, accepts additional zfb flags
pnpm circuit:generate          # regenerate component pages and preflight report
pnpm circuit:models            # publish reviewed public models
pnpm previews:generate         # render SVGs with the pinned KiCad toolchain
pnpm check                     # generated drift, CAD/model parity and site types
pnpm build                     # validate, publish models, generate and build
pnpm check:site                # publication, scan, link and fragment gates
pnpm b4push                    # complete guarded local repository quality gate
```

Run `pnpm install --frozen-lockfile` from the repository root; the root lockfile
pins the circuit package (with its one reviewed checker patch) and the zudo-doc scaffold. Deployment uses the Cloudflare
adapter in `wrangler.toml` and the repository workflows; local builds do not deploy.
A successful doc build does not validate hardware or authorize an order. The root
`pnpm b4push` is wrapped by one outer heavy guard when available. Browser checks run
separately through the guard; report `SKIP`, exit 4, contention and deferred results
accurately rather than as passes.

## Authoring rules

Write English. Every page requires frontmatter `title`; optional `sidebar_position`
controls order. Start body headings at `##`, since the title renders the h1.
Use `.md` for prose and `.mdx` for JSX navigation/interactive components.

`<CategoryNav category="..." />` renders a category landing page. Admonitions such
as `<Note title="...">` work in plain `.md`; put Markdown content on separate lines.
Use Mermaid fences for block diagrams and net tables for actual connectivity.

Internal source links use the target `.md` or `.mdx` extension. Generated component
links use canonical `/docs/components/.../` routes and explicit evidence anchors.
Static assets use root paths such as `/circuits/name.svg`. Place images as standalone
Markdown paragraphs so enlarge controls can work.

Escape `<` in prose as `&lt;`, and keep literal braces inside inline code. Do not
make unsupported electrical claims in summaries: distinguish targets, typical data,
guaranteed limits, project connectivity, programmed state and measured behavior.

For a local docs URL, read the matching source under `src/content/docs/`; browser
checks remain useful when verifying rendered navigation, interactions or layout.

## Maintain current owners and historical routes

On an adopted design change, update `project/current-state.md` with dated artifact/check/physical state, the affected
variant design page with source/interface responsibilities, and `architecture/release-readiness.md` if gates change.
Update `circuit/DOCUMENTATION_MAP.md` for ownership/migration changes. Entry READMEs link these owners.
`zfb.config.ts` owns the six supported groups and matching `categoryMatch` values; dropdowns include landing children.
Curated indexes define current recommendations; retained legacy pages can still appear in category sidebars.
Use the inventory/config/preflight for current counts: five inventory inputs A/B/P/P15/B20, four A/B/P/P15
pure-Python schematic regeneration gates, B20 projection `board_b20_components.py`.
