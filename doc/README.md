# zudo-pd documentation

A component-first zudo-doc site built with zfb, MDX and Preact. Layout and navigation
come from the framework; this directory owns project content and the reviewed
component publication pipeline.

```sh
pnpm install
pnpm dev       # site :4321, history :4322, component watcher
pnpm build     # models + component records + static site in dist/
pnpm b4push    # complete local documentation validation
```

The current reading path is **Getting Started → Architecture → Components → How-To**.
The Archive groups previous overview, diagnosis and learning pages at their stable
URLs. Old claims never override the current inventory or schematic.

`src/content/docs/components/` is generated from repo-root `.claude/skills/` evidence.
Edit exact records or `component-docs/`, then regenerate; do not hand-edit generated
pages, SVG previews or model manifests. See [component-docs/README.md](component-docs/README.md)
and [CLAUDE.md](CLAUDE.md) for authoring and validation details.

`zfb.config.ts` owns site settings and navigation. `pages/` contains package route
stubs. `src/chrome-bindings.tsx` registers the component previews. `public/` contains
reviewed static assets; deployment configuration remains in `wrangler.toml`.
