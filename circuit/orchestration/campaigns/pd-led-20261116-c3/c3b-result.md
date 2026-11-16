# C3b bounded result — #315

**State: BLOCKED for routing acceptance.** The source-bound crosswalk is in
`c3b-source-crosswalk.json` on the exact accepted C3a base
`123a26ec7327f3605dd19990472a3e99b655bb85`. It records existing ST and UMW
text aliases and the retained Nexperia/LCSC binding for `PESD24VS1UB,115`.
It is not canonical identity adoption or permission to merge evidence payloads.
The ST record now states both the earlier failed manufacturer retrievals and
the later direct primary retrieval of byte-identical DS12499 on 2026-11-09;
its current `fact-stusb-manufacturer` verdict remains `UNSOURCED`.

The current `resolve_bundle_route` implementation in
`.claude/skills/component-spec-audit/scripts/validate.py` matches the bare
`PESD24VS1UB` alias inside `PESD24VS1UB,125` (and other comma suffixes). On
the unchanged C3a base, both `PESD24VS1UB,115` and the wrong order code
`PESD24VS1UB,125` resolve to `rec-pesd24vs1ub-c85382`. The owner manifest
requires the bare part name in the route. Moya then extended the allowlist
to the local `scripts/validate.py` resolver. A narrow local correction and
positive/negative tests passed strict local validation and all 54 focused
tests, including wrong suffix alone, with C85382, beside a valid suffix,
extended suffix, case/whitespace, ordinary punctuation and unaffected routes.
However, the pinned `@takazudo/zudo-circuit-doc` 0.3.0 package has a separate
resolver in `python/circuit_evidence/routing.py`. `pnpm circuit:check` failed
on its bundle validation: `route-pesd24vs1ub-c85382: negative query unexpectedly
resolves: PESD24VS1UB,125`. The package/patch path is outside the expanded
write allowlist. The failing local routing candidate was not committed; no
false acceptance or weakened negative assertion was pushed.

Preflight: the C3a remote and checkout matched the exact accepted SHA; the
new C3b branch did not exist remotely. The seven C3a source-lock hashes matched.
PR #307 remained open at `9312dc627df2de22d1ac44a3a05fbcb207665b3e`
and owns separate B20 files. C4a uses disjoint files. No competing local writer
was found in this fresh checkout; external live sessions cannot be proven from
this VM. The root push workflows are restricted to `main`; no PR was opened.

Baseline `python3 .claude/skills/component-spec-audit/scripts/validate.py --strict`
passed: 129 lines, 16 candidates, 41 bundles. The initial focused
`test_validate.py` suite passed 53 tests; the corrected local candidate
passed 54. JSON syntax, seven retained C3a
source-lock hashes and `git diff --check` passed. An inventory readback showed
129 lines, 467 placements and 12 DNP placements. The direct resolver probe above
failed the requested wrong-code negative on the base. The initial
`pnpm circuit:check` could not start because pnpm could not create
`/home/agent/.local/share/pnpm` (`ENOENT`). The corrected attempt installed
the pinned pnpm 11.5.2 and workspace dependencies using workspace-local
Corepack/pnpm homes and two CPU cores. `pnpm circuit:check` then ran and failed
at the package resolver as described above. Native CAD, CI, PR, merge, deployment and
physical checks are **NOT RUN** by task contract. Canonical inventory and DNP
placement files were not edited.

Next safe action for Moya: authorize a narrow fix to the pinned package resolver
or its reviewed patch, then align the local resolver, add the positive and
wrong-order-code negative tests, and rerun strict validation and
`pnpm circuit:check` before independent exact-head review.
Keep the SMAJ footprint and globally conflicting evidence payloads on hold.
