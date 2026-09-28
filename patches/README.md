# Circuit-doc 0.1.0 compatibility

Removal tracker: [zudo-pd #210](https://github.com/Takazudo/zudo-pd/issues/210).
The runtime request is `^0.1.0`; the root lock resolves the npm 0.1.0 tarball with
its registry integrity and its circuit-package patch hash. This patch edits the **shipped**
`lib/*.js`, their matching `.d.ts`, Python modules and packaged contract schema.
It does not import the upstream TypeScript source or the project validator.
Source review pin: `Takazudo/zudo-circuit-doc@5d0e2b630776489d394be341586b889dfe0d1cb8`.

Every hunk belongs to these linked contract groups (also linked in module headers):

| Upstream report | Shipped modules and changes |
| --- | --- |
| [#103](https://github.com/Takazudo/zudo-circuit-doc/issues/103) | `config/{define,schema,resolve,map}`, `validate/resolved-config`, Python `inventory/{common,led_generator_v1}`, `provider/v1/{evidence,index}`, `core/view-model`, `core/render/{shared,catalog,record}`: contained board/spec declarations; finite value-field MPN configuration; placement DNP and mixed state, with legacy line clients retained. |
| [#104](https://github.com/Takazudo/zudo-circuit-doc/issues/104) | `contract/schema.json`, config and resolved transport, Python `aggregate/orchestrator`, `provider/v1/{paths,evidence,index,canaries}`: candidate identity/owner validation, all owner bundles, unique global evidence IDs, explicit cross-partition rejection, and publication of inventory records only. |
| [#105](https://github.com/Takazudo/zudo-circuit-doc/issues/105) | `config/map`, `core/{publication,reference-descriptor,view-model}`, `provider/v1/{references,index,model-assets}`, `core/render/record`, `ui/component-references`, `scan/built-references`: disjoint selections/exceptions, independently unavailable cards, strict declared local files, nullable types and built-site assertions. |
| [#106](https://github.com/Takazudo/zudo-circuit-doc/issues/106) | `provider/v1/{index,integration,canaries}`, `core/view-model`, scanner positive controls and CLI scanner: nullable denied owners/package membership and matrix-aware denied owner canaries. |
| [#107](https://github.com/Takazudo/zudo-circuit-doc/issues/107) | `scan/artifacts`: configured generated-root exclusion; extra public files scanned; only reviewed canonical footprint hash fields excused in SITE manifests after recomputation and full path/symlink proof. OWNED canaries and other manifest fields remain strict. |

`circuit/publication/` retains the complete selection (59 documents and one honest
exception), 99 field decisions, the unchanged dated document audit and project
glosses. `assets.json` is the scaffold bootstrap allowlist; final site publication
and deliberate existing public assets are reconciled in #207.

`pnpm circuit:prepare` and `pnpm circuit:check` run the project's strict validator
and strict forward tests before invoking package operations. The installed CLI's
validator remains an additional contract gate. `circuit:doctor` is diagnostic.
The root workspace lock resolves both the repository and `doc/` to the same
patched installed modules. The circuit runtime patch and scaffold heading-extractor
patch are separate package boundaries; the old `doc/component-docs/` implementation
was retired in [zudo-pd #208](https://github.com/Takazudo/zudo-pd/issues/208). Root
runtime peers remain pinned to the scaffold versions for meaningful SSR tests.

## Zudo-doc 5.27.0 heading parity

The separate `@takazudo/zudo-doc` 5.27.0 patch is tracked for removal by
[zudo-pd #211](https://github.com/Takazudo/zudo-pd/issues/211). Its source behavior
is reviewed in [zudolab/zudo-doc #4428](https://github.com/zudolab/zudo-doc/issues/4428).
It aligns the built heading extractor with the zfb/CommonMark headings used by this
site, including inline code, character references and the depth window. The retained
strict source-link, built-fragment and redirect checks exercise the installed
scaffold behavior. Do not replace these checks with an allowlist or a looser link
warning rule.

The circuit package patch is temporary compatibility work tracked by
[zudo-pd #210](https://github.com/Takazudo/zudo-pd/issues/210). The scaffold removal
tracker is #211. Follow-up package work covers foreground Chrome scheduling
([#108](https://github.com/Takazudo/zudo-circuit-doc/issues/108)) and responsive
reference-card layout ([#109](https://github.com/Takazudo/zudo-circuit-doc/issues/109)).
The package's enlarged-media contract deliberately uses an empty image alt when the
dialog supplies the full accessible label; the project browser smoke asserts that
contract under [#110](https://github.com/Takazudo/zudo-circuit-doc/issues/110). This
is not a local #110 patch. Keep the project regressions enabled until released
upstream versions supply the contracts owned by each package.

`pnpm test:compatibility` exercises installed package files, never a source clone:
real CLI doctor/validate/generate/check/models/footprints, idempotency, exact corpus
identities/counts, 313 canonical evidence/spec file hashes, negative candidate
source/fact/pin-map mutations, mixed DNP, both finite MPN exceptions, old explicit
evidence anchors, independent SSR/descriptor cards, nullable-model CLI workflow,
missing/corrupt/ambiguous local models, denied owners, generated-root subtraction,
planted MDX/search/dist/public leaks and malformed/unproved/symlinked hash proofs.
The TypeScript consumer smoke checks the shipped declarations in strict mode;
`skipLibCheck` avoids checking unrelated dependency implementation declarations.

The canonical hash fixture is a closed migration baseline, **not** a regeneration
workflow. Changes require an independently reviewed evidence diff with every
changed field identified. Its `files` map is the exact list of hash-covered paths.
The candidate-only evidence stays on disk and under both validators; it is never
silently treated as inventory or as an independent reason to suppress a leak.

The root command surface owns strict project checks, generation, CAD/model parity,
site publication/link checks and guarded b4push. The retained project browser smoke
covers the document-gap record, resolved cards, model and footprint dialogs,
keyboard/focus/no-JS states, the illustrative inductor note and all 12 named
representatives. The PR workflow keeps the Cloudflare preview alias; the production
workflow keeps its guarded domain deployment. Neither workflow deploys from a local
build. Canonical evidence, hardware designs and generated component pages remain
owned by their existing project workflows and contracts.
