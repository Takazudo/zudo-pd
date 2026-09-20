# Documentation guidance

This is a zudo-doc site using zfb, MDX, Tailwind and Preact. Framework packages own
layout and chrome. `zfb.config.ts` owns the project configuration, using the `sumi`
theme. The route stubs under `pages/` stay package-shaped; custom preview components
are registered through `src/chrome-bindings.tsx`.

## Content ownership

- `getting-started/`: project brief, evidence limits and repository entry points.
- `architecture/`: current board roles, interfaces, component map and release gates.
- `components/`: generated catalog, exact records and integration evidence; never hand-edit.
- `how-to/`: repeatable design and manufacturing procedures.
- `archive/`: guide to historical material. `overview/`, `inbox/`, `learning/` and
  `misc/` keep stable URLs and explicit historical banners.

Do not append new current-state corrections to historical narratives. Update the
current page and link it from the archive when useful. Preserve historical sources
and diagnostic records, including their evidence anchors.

The catalog is a reviewed projection of repo-root `.claude/skills/`. Its publication
matrix deliberately leaves raw skills unpublished (`claudeResources: false`). Read
`component-docs/ARCHITECTURE.md` before changing the projection. Generated evidence
already carries source provenance, so generated-page git history is excluded from
the history UI.

## Commands

```sh
pnpm dev                       # zfb :4321 + history :4322 + component watcher
pnpm dev:zfb                   # zfb alone, accepts additional zfb flags
pnpm generate:components       # regenerate human component pages
pnpm generate:models           # copy reviewed public models
pnpm generate:footprint-previews # regenerate SVG geometry with the KiCad toolchain
pnpm check                     # TypeScript
pnpm build                     # generated assets/pages + static HTML
pnpm b4push                    # component tests, assets, build, links and publication scans
```

Use the committed lockfile. Deployment is configured by `wrangler.toml` and the
repository workflow; local builds do not deploy. A successful doc build does not
validate hardware or authorize an order.

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
