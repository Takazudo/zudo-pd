# ZUDO_DEPS_PINS

Provenance for artifacts vendored or generated from first-party upstreams.
Update pins with the reconciled artifacts only after verification succeeds.

## zudo-doc (doc route stub, home route, tsconfig, global CSS)
- repo: zudolab/zudo-doc
- what: scaffold-derived host glue with the zudo-circuit-doc integration lines layered on top
- files: doc/pages/docs/[[...slug]].tsx, doc/pages/index.tsx, doc/tsconfig.json, doc/src/styles/global.css
- source: packages/create-zudo-doc/templates/base/{pages/docs/[[...slug]].tsx,pages/index.tsx,tsconfig.json,src/styles/global.css}, as emitted by create-zudo-circuit-doc 0.2.1 (which re-derives them from create-zudo-doc 9.1.4 published bytes)
- track: releases (create-zudo-doc / zudo-doc are released together)
- pinned: 054c1dabb5810afa24485a5431bce094b14fae21 (create-zudo-doc@9.1.4 npm gitHead)
- updated: 2026-11-08
- sync: generate an external create-zudo-doc@9.1.4 default scaffold and an external create-zudo-circuit-doc@0.2.1 reference project with --yes --no-git, then diff the files above; never run either initializer inside this repository
- notes: The route stub carries the docHistory feature patch (`DocHistoryBoundary as DocHistory` merged over the chrome bindings) plus one added line, `import "../lib/_circuit-doc-islands";`, whose seed module imports `@takazudo/zudo-circuit-doc/islands` so the footprint and model preview islands hydrate (this replaces the 5.x static island imports tracked in #126). global.css adds `@import "@takazudo/zudo-circuit-doc/styles.css";` after the zudo-doc feature CSS and keeps an empty `:root` override slot; the design-token panel stylesheet is not imported because the panel is off (#125). tsconfig is byte-identical to the reference. See doc/SCAFFOLD.md for the default-feature and extension inventory.

## zudo-doc (link checker)
- repo: zudolab/zudo-doc
- what: default scaffold link diagnostic CLI, copied without modifications
- files: doc/scripts/check-links.js
- source: packages/create-zudo-doc/templates/base/scripts/check-links.js
- track: releases (create-zudo-doc / zudo-doc are released together)
- pinned: 054c1dabb5810afa24485a5431bce094b14fae21 (create-zudo-doc@9.1.4 npm gitHead)
- updated: 2026-11-08
- notes: Byte-identical to the 9.1.4 scaffold output (unchanged from 5.27.0). Invoked by pnpm check:links (advisory) and pnpm check:anchors (strict anchors, after build in b4push and CI). Keep the strict generated-reference and CI warning gates.

## zudo-circuit-doc (runtime, registry-pinned)
- repo: Takazudo/zudo-circuit-doc
- what: `@takazudo/zudo-circuit-doc` 0.3.x in the root and doc/ manifests; replaces the retired project-local doc/component-docs engine
- files: package.json, doc/package.json, circuit.config.ts, circuit/publication/*.json, circuit/policy.json
- source: n/a (registry release); migration reference was fixtures/led at a2b427a89867fc909248b0d1717d7da4fda44f27, whose corpus is pinned to this repository at 194d8a297e3545588197342130c3111a66c10973
- track: releases
- pinned: 0.3.0 (lockfile)
- updated: 2026-11-08
- notes: Publication selection, document verification and policy data were copied from the fixture only after proving them equal to this repository's live selection.ts and gates; the evidence itself was never touched. With the legacy marker retained, all 39 generated pages were byte-identical to the retired engine's output; the preflight changed only `viewModelVersion` 1 -> 2 and moved to circuit/generated/preflight.json.

## zfb family (registry-pinned, not vendored)
- repo: Takazudo/zudo-front-builder
- what: `@takazudo/zfb`, `-runtime`, `-md-wasm`, `-adapter-cloudflare`, exact-pinned in doc/package.json
- files: doc/package.json
- source: n/a (registry release)
- track: releases
- pinned: 5.2.2
- updated: 2026-11-08
- notes: Keep the four packages aligned with the zudo-doc 9.1.4 / zudo-circuit-doc 0.3 family (runtime peers ^9.1.3 / ^5.2.2). Node 24 (>=24 <25) is required. The adapter still emits dist/.assetsignore with `_worker.js` and `_zfb_inner.mjs`.
