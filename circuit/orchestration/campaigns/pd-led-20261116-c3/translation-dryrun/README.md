# C3d in-memory translation feasibility check

This is the next decision-independent verification after the independently accepted C3c proposal at `c6d493ca8ee55f7b396be699e586c4f8ad85f535`. The accepted [PD/LED plan](../../../pd-led-unification.md) requires one exact-component corpus, but identity/CAD/DNP/publication decisions still block canonical adoption. This check stays on isolated branch `codex/c3d-translation-dryrun-20261116-01` and owns only this new directory. It does not create an active catalog or change any owner bundle.

`verify.py` loads the source-bound C3c proposal, recomputes it against the 393 locked JSON inputs, then applies its structured ID map and 27 paired arithmetic expressions to an **in-memory** LED copy. It checks each old value before replacement, verifies that only the listed ID/expression leaves changed, parses each proposed expression and compares its symbols with translated dependency IDs, checks for PD collisions and recomputes complete structured reference closure. `result.json` is deterministic output from that check. Run:

```sh
python3 circuit/orchestration/campaigns/pd-led-20261116-c3/translation-dryrun/verify.py
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261116-c3/translation-dryrun -p 'test_*.py' -v
```

Result: 795 translated definitions, 3,896 changed structured references, 27 expression rewrites for review, zero unresolved translated structured references and zero unapproved changed leaves. All 463 textual ID locations remain held. Three focused tests passed (maximum child RSS 34,616 KiB); the six upstream C3c tests, source-lock regeneration and `pnpm circuit:check` also passed. Checks used `taskset -c 0,1` and an inherited 4 GiB per-process address-space limit. The largest measured child RSS for `pnpm circuit:check` was 115,212 KiB; aggregate peak across simultaneous children was not measured.

This dry run does not invoke the pinned validator on a merged active corpus, resolve equal-ID payload conflicts, approve the proposed ID syntax in generated routes, review the 463 textual replacements, reconcile exact part/CAD/SMAJ identities or LED placement DNP, or change PD's publication policy. Original LED and PD JSON bytes, historical receipts, P15 owner/consumer, #307, private vendor material and all hardware holds remain intact. The next gate is independent exact-head review of this isolated verification, followed by Moya's identity/CAD and serialized canonical implementation decisions. Native, full build, CI, PR, merge, deployment and physical checks were not run.
