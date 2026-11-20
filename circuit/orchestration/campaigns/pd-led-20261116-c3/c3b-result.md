# C3b bounded result — #315

**State: REVIEW_READY; independent exact-head review pending.** This task builds
on accepted C3a `123a26ec7327f3605dd19990472a3e99b655bb85` on the exclusive
`codex/c3b-identity-crosswalk-20261116-01` branch. The source-bound crosswalk
maps existing ST and UMW maker text aliases and the retained Nexperia/LCSC
`PESD24VS1UB,115` order-code identity. Earlier ST primary retrieval attempts
failed, but direct byte-identical DS12499 retrieval on 2026-11-09 is recorded;
`fact-stusb-manufacturer` retains its existing `UNSOURCED` verdict.

## Routing and patch

The PD PESD route declares `PESD24VS1UB,115` and wrong-code negative fixtures.
Both the project-local validator and pinned `@takazudo/zudo-circuit-doc` 0.3.0
package resolver reject unknown attached numeric order suffixes before bare-MPN
or LCSC fallback. An accepted spaced suffix such as `PESD24VS1UB, 115` is
normalized to its declared alias before the existing manufacturer qualifier
checks. Thus `PESD24VS1UB, 115 from/by OtherVendor` rejects, while the same
query from/by Nexperia resolves. Ordinary comma punctuation, bare aliases,
shared-MPN selection, board qualifiers, empty-LCSC routes and inventory routing
retain their behavior.

The project-local package patch contains the unchanged three prior checker/Mac
browser hunks plus only the Python bundle-routing hunk. The lockfile changes
only that patch hash. Version 0.3.0 and every dependency version remain pinned;
no shared package was published. The historical compatibility and runtime
baselines remain frozen. Current-evidence overlays add the actual SHA256 for
only the two changed local validator files and the PESD routing file, plus only
the PESD aliases semantic digest.

## Preflight and final checks

The C3a remote remained at the accepted SHA. C3b remote and checkout matched
the previous head before edits. PR #307 remained open at
`9312dc627df2de22d1ac44a3a05fbcb207665b3e`, with disjoint B20 ownership.
Seven C3a source-lock hashes matched. No competing local writer was observed;
external sessions cannot be proved from this checkout. Topic-branch push
workflows were inspected and are restricted to `main`; no PR was opened.

- Clean frozen install, pinned pnpm 11.5.2, two CPU cores and workspace-local
  Corepack/pnpm homes: **PASS** after the final package patch.
- Strict component validator and cross-component forward checks through
  `pnpm circuit:check`: **PASS**. Package validation reports 129 lines,
  467 placements, 16 candidates, six integration cases and nine negative routes.
- Focused Python `test_validate.py`: **54 PASS**, including paired spaced
  `from`/`by` vendor cases.
- Installed-package `compatibility-routing.test.mjs`: **2 PASS**, including CLI
  parity and the same qualifier cases.
- `pnpm test:compatibility`: **17 PASS**, including retained canonical-byte
  baselines and TypeScript compatibility checking.
- `node --test circuit/tests/runtime.test.mjs`: **6 PASS**, including the PESD
  alias semantic overlay and installed patch target assertion.
- Seven C3a source locks, unchanged original patch hunks, lock patch-hash-only
  diff, inventory **129 lines / 467 placements / 12 DNP**, JSON and Git diff
  checks: **PASS**.

No component evidence payload, DNP placement, SMAJ footprint, CAD, publication
selection or vendor source was changed. Native CAD, CI, PR, merge, deployment
and physical checks are **NOT RUN** by task contract. Keep the SMAJ footprint
and all globally conflicting shared evidence payloads on hold. Moya's next
step is independent exact-head review before any serialized integration.
