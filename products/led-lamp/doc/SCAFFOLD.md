# Documentation scaffold maintenance

Baseline: `create-zudo-doc@9.1.4`, released with `@takazudo/zudo-doc@9.1.4`, as
re-derived by `create-zudo-circuit-doc@0.2.1`. The release source is
`054c1dabb5810afa24485a5431bce094b14fae21` in `zudolab/zudo-doc`.
`ZUDO_DEPS_PINS.md` tracks copied files. The 5.27.0 baseline
(`50cbd5c6c9e5a795d72a74a855e105e4939d4eab`) is historical.

## Default feature inventory

| Scaffold feature enabled by default | Site integration |
| --- | --- |
| Search | `search` header item; package search index |
| Sidebar filter | Built into the package sidebar |
| Sidebar resizer | `sidebarResizer: true` |
| Sidebar toggle | `sidebarToggle: true` |
| TOC toggle | `tocToggle: true` |
| Document history | `docHistory: true`, route binding and local history server |
| LLM text exports | `llmsTxt: true` |
| Image enlargement | `imageEnlarge: true` |
| Asset viewer | `assetViewer: true`; package-owned `/files/` routes |
| Dynamic page transitions | `dynamicPageTransition: true` |
| Footer copyright | Existing project attribution |

The theme pack is pinned to `default` (Classic) with `themePacks: ["default"]`;
zudo-doc 9 would otherwise default to Graphite and ship every pack. Light/dark
mode uses the package Appearance menu (Light, Dark, System), with System following
the device preference. This single-locale site
uses GitHub, theme, and search header controls. Asset listing and asset indexing
in search/LLM exports remain off, matching upstream defaults. Files are already
published under `public/assets`; the viewer adds a presentation route.

## Intentional project extensions

- Preserve the site name, domain, navigation and footer attribution.
- Keep CJK handling and repo-root Claude resource publication. The `doc/.claude`
  tooling directory remains outside that publication source.
- Keep the body-foot history strip and component-history exclusions: generated
  component pages carry evidence provenance rather than useful MDX edit history.
- Keep the `circuitDocMdxExtras` registration in `src/chrome-bindings.tsx` and the
  docs route's `import "../lib/_circuit-doc-islands";` seed import. The generated
  route is reconciled, never blindly overwritten.
- Keep the zudo-circuit-doc component, footprint and model generation, the enclosure
  generator and their validation gates.
- Keep the Cloudflare adapter and deployment configuration, plus dependencies used
  by those extensions. New scaffold dependencies are a minimum, not a removal list.
- Keep the package theme CSS chain followed by `@takazudo/zudo-circuit-doc/styles.css`.
  The former project-local `.zld-*` component styles are retired with the local engine.
- Keep `.zudo-doc/` ignored: this release stages package routes there for nested
  pnpm consumers.

Scaffold scripts use zudo-doc's `run-parallel` to run development services. The
project also starts the zudo-circuit-doc watcher and generates component docs first.
`check:images` is the package image/media validator. `check:links` is the copied
scaffold link checker. `check:anchors` applies its strict anchor check after the
build in both local validation and CI. Existing checks additionally cover
hand-authored route warnings and generated component references.

Optional locales, design-token panel, theme switcher, versioning, sitemap, tag
features, Codex publication, and desktop wrappers are not enabled by this refresh.

## Refresh procedure

1. Resolve every `@takazudo/*` dependency on its existing release channel, compare
   published tarballs from lockfile versions, and check peers as a family
   (zudo-doc, zfb and zudo-circuit-doc).
2. Generate a fresh site outside this repository using the exact released
   `create-zudo-doc` version with `--yes --no-install --no-git`, and a separate
   `create-zudo-circuit-doc` reference project for the integration lines.
3. Compare feature defaults, generated config, route stubs, CSS, scripts and
   TypeScript configuration. Reapply the extensions above when reconciling.
4. Install from the repository root, run the guarded `pnpm b4push`, image/link
   diagnostics, `pnpm test:browser` (zudo-circuit-doc `check-browser` with shell and
   search assertions), the enclosure viewer smoke, and dev deep routes.
5. Commit regenerated Claude-resource pages together with instruction changes.
   Update the provenance pin only after verification succeeds.

## Escaped-underscore anchors verified fixed

zudo-doc 5.27.0 fixes the TOC mismatch reported in
[zudo-doc issue 4380](https://github.com/zudolab/zudo-doc/issues/4380).
The refreshed checker shares the package heading extractor, including h5/h6 IDs.
The upgrade reduced the built site's 272 invalid anchors to zero. The four
authored links corrected in the previous refresh remain intact.

`check:anchors` now prevents this class of defect from passing local validation
or deployment CI. No local package patch or anchor allowlist was needed.

## Mobile Appearance Escape remains upstream

In 5.27.0, pressing Escape in the mobile drawer's Appearance menu closes both
menu and drawer, preventing focus restoration to the Appearance trigger.
[zudo-doc issue 4393](https://github.com/zudolab/zudo-doc/issues/4393) tracks the
nested Escape handling defect. Theme selection and System persistence work;
this does not affect the repaired TOC anchors. Keep the package implementation
until the upstream fix is released.
