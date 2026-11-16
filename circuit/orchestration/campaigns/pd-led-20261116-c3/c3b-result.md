# C3b bounded result — #315

**State: BLOCKED for routing acceptance.** The source-bound crosswalk is in
`c3b-source-crosswalk.json` on the exact accepted C3a base
`123a26ec7327f3605dd19990472a3e99b655bb85`. It records existing ST and UMW
text aliases and the retained Nexperia/LCSC binding for `PESD24VS1UB,115`.
It is not canonical identity adoption or permission to merge evidence payloads.

The current `resolve_bundle_route` implementation in
`.claude/skills/component-spec-audit/scripts/validate.py` matches the bare
`PESD24VS1UB` alias inside `PESD24VS1UB,125` (and other comma suffixes). On
the unchanged C3a base, both `PESD24VS1UB,115` and the wrong order code
`PESD24VS1UB,125` resolve to `rec-pesd24vs1ub-c85382`. The owner manifest
requires the bare part name in the route, so editing `routing.json` and adding
a focused test cannot make the wrong-code negative pass. The exact write
allowlist excludes the resolver. No routing or test file was changed; no
false negative control or weakened assertion was committed.

Preflight: the C3a remote and checkout matched the exact accepted SHA; the
new C3b branch did not exist remotely. The seven C3a source-lock hashes matched.
PR #307 remained open at `9312dc627df2de22d1ac44a3a05fbcb207665b3e`
and owns separate B20 files. C4a uses disjoint files. No competing local writer
was found in this fresh checkout; external live sessions cannot be proven from
this VM. The root push workflows are restricted to `main`; no PR was opened.

Baseline `python3 .claude/skills/component-spec-audit/scripts/validate.py --strict`
passed: 129 lines, 16 candidates, 41 bundles. The existing focused
`test_validate.py` suite passed 53 tests. JSON syntax, seven retained C3a
source-lock hashes and `git diff --check` passed. An inventory readback showed
129 lines, 467 placements and 12 DNP placements. The direct resolver probe above
failed the requested wrong-code negative. `pnpm circuit:check` was attempted
once but did not start its check: pnpm's dependency setup could not create
`/home/agent/.local/share/pnpm` (`ENOENT`). New positive and wrong-order-code
negative routing tests are **NOT RUN / NOT ADDED** because the latter cannot pass
within the admitted write surface. Native CAD, CI, PR, merge, deployment and
physical checks are **NOT RUN** by task contract. Canonical inventory and DNP
placement files were not edited.

Next safe action for Moya: extend the allowlist to the resolver and independently
review a narrowly scoped comma-suffix refusal rule; then add the positive and
wrong-order-code negative tests and rerun strict validation and `pnpm circuit:check`.
Keep the SMAJ footprint and globally conflicting evidence payloads on hold.
