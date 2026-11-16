# C3b bounded result — #315

**State: BLOCKED on retained baseline scope; implementation is not accepted yet.**
The branch is based on independently accepted C3a
`123a26ec7327f3605dd19990472a3e99b655bb85`. The source-bound crosswalk
maps existing ST and UMW manufacturer text aliases and the Nexperia/LCSC
`PESD24VS1UB,115` order-code binding. ST's later direct primary retrieval is
recorded, while `fact-stusb-manufacturer` retains its `UNSOURCED` verdict.
No evidence payload, DNP placement, SMAJ footprint, CAD, publication selection
or vendor source was changed.

## Routing change

The PD PESD route now declares the exact `,115` alias and wrong-suffix negative
fixtures. Both the project-local `validate.py` and the pinned
`@takazudo/zudo-circuit-doc` 0.3.0 Python bundle resolver reject an unknown
attached numeric order suffix before bare-MPN or LCSC fallback. The guard runs
only for bundles with declared comma-qualified MPN aliases. Bare identities,
ordinary comma punctuation, shared-MPN manufacturer selection, board qualifiers,
empty-LCSC routes and inventory routing retain their behavior. The package is
patched locally; its existing checker and two Mac browser hunks and all package
versions remain intact. No shared package was published.

## Preflight and checks

The C3a remote stayed at the accepted SHA; the C3b remote matched the prior
partial head before this attempt. PR #307 remained open at
`9312dc627df2de22d1ac44a3a05fbcb207665b3e`; its B20 paths do not overlap.
No competing local writer was found. Seven C3a source-lock hashes matched.
Root topic-branch pushes do not trigger Actions at the inspected workflow revision.

- Clean `pnpm install --frozen-lockfile` with pinned pnpm 11.5.2 and a
  workspace-local Corepack/pnpm home: **PASS** after the final patch hunk.
- Strict project component validation and 54 focused Python tests: **PASS**.
- New installed-package routing and CLI tests: **2 PASS**, including bare,
  exact, wrong, mixed and extended order codes; C85382 fallback; case/spacing,
  punctuation, shared MPN/manufacturer, board qualifiers and empty-LCSC routes.
- `pnpm circuit:check`: **PASS** (129 lines, 467 placements, 16 candidates,
  six integration cases, nine negative routes).
- TypeScript compatibility type check: **PASS**.
- `pnpm test:compatibility`: **16 PASS / 1 FAIL**. The retained canonical-byte
  check pins old SHA256 values for the necessarily changed
  `.claude/skills/component-spec-audit/scripts/test_validate.py` and
  `validate.py`. The first mismatch is `test_validate.py`.
- `node --test circuit/tests/runtime.test.mjs`: **5 PASS / 1 FAIL**. Its
  semantic baseline pins the old `pesd24vs1ub-c85382.aliases` hash and fails
  after the required `,115` alias is added.
- The canonical inventory remains **129 lines / 467 placements / 12 DNP**.
  The reviewed PESD `routing.json` SHA256 is recorded in
  `circuit/tests/current-evidence-baseline.json`; its other entries are intact.

The exact #315 allowlist permits only the PESD routing hash in
`current-evidence-baseline.json`, and does not permit
`circuit/tests/current-evidence-semantic.json`. Clearing these two retained
baseline failures therefore requires Moya to admit the two local validator-file
hash overrides and the PESD alias semantic hash in the current-evidence
baselines. The historical compatibility baseline itself should remain frozen.
No baseline assertion was weakened or bypassed.

Native CAD, CI, PR, merge, deployment and physical checks are **NOT RUN** by task
contract. Independent exact-head review and integration remain pending. Keep
SMAJ footprints and all conflicting shared evidence payloads on hold.
