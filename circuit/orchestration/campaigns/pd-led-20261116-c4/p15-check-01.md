# C4a P15 same-repository reference check — attempt 01

- Tracker: [#314](https://github.com/Takazudo/zudo-pd/issues/314), child of [#308](https://github.com/Takazudo/zudo-pd/issues/308).
- Manager and intended integrator: Moya. Implementer: this bounded Codex Cloud attempt. Independent reviewer: assigned by Moya after delivery.
- State: REVIEW_READY after commit and push; adoption: not integrated; release: not accepted.
- Source: accepted isolated C3a `123a26ec7327f3605dd19990472a3e99b655bb85`, including accepted C2 `6945f8d4ccd969531b38cb338cecafe224bb2cfb`. The original LED consumer owner pin is `8af9e5569c2534c03ce132515d1ec11f4c3f83d3`.
- Branch: `codex/c4a-p15-check-20261116-01`, created exclusively for this task. Only this record, `circuit/scripts/check-led-p15-reference.sh`, and `circuit/tests/led-p15-reference.test.mjs` are owned writes.
- Attempt budget: one attempt, 30 minutes, at most 2 CPU / 4 GiB. Guest cgroup reports 4 CPU quota and 16 GiB memory limit; disk had about 30 GiB free. Account-wide usage and model selection telemetry are unavailable to this worker.

## Change and source boundary

The root entry runs the imported LED consumer verifier and existing PD P15 owner verifier against the same repository's complete Git history, once at the immutable original owner pin and once at the accepted C2 commit. It checks that the consumer still names the original PD owner, record path, and pin. The verifiers inspect committed owner blobs; the LED verifier also checks the preserved local historical LED Board P bytes. The entry accepts no arguments, so a caller cannot silently request `--local-only` or substitute a revision.

The original consumer record, PD owner record, seven owner artifacts, 151-entry frozen package, native CAD, evidence corpus, and independent PD20 #307 are unchanged. The frozen source-lock report is informational for later changes, not a new package replay. Source identity does not establish programming, electrical, mechanical, manufacturing or physical acceptance.

## Checks and limitations

- Before edits: `python3 -m unittest discover -s products/led-lamp/scripts/checks -p 'test_verify_p15_reference.py'` — 10 passed.
- Before edits: `python3 -m unittest discover -s scripts/pcb/board-p15 -p 'test_verify_shared_reference.py'` — 17 passed.
- Before edits: direct execution of both Python verifiers at `8af9e5569c2534c03ce132515d1ec11f4c3f83d3` and `6945f8d4ccd969531b38cb338cecafe224bb2cfb` — all four returned `SOURCE IDENTITY MATCH`. The owner verifier reported seven matching artifacts at each revision.
- After edits: `node --test circuit/tests/led-p15-reference.test.mjs` — 4 passed, including root and unrelated working directories, missing revision/history, mismatched consumer and owner records, and argument refusal.
- `git diff --check` — passed.
- `pnpm circuit:check`, broad test/build/site gates, native tools, CI, PR, merge, deploy and hardware actions — NOT RUN under the focused-check-only task contract. Full fixed package replay — NOT RUN without the original local-only `populated-stack.step`.

Independent review should inspect the final branch SHA and these three paths, then Moya can decide serialized adoption. The worker's green source checks do not self-approve integration.
