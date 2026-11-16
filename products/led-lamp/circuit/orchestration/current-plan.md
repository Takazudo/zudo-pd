# zudo-led-lamp orchestration mapping

Policy date: 2026-11-12. Inspected main: `49a6c316908f2668460d9707872e1641af41a855` (PR #152 merged). Proposed mapping only; no worker or computation launched. Refresh source/issues before use. Follow [WORKFLOW.md](../WORKFLOW.md), [ORCHESTRATION.md](../ORCHESTRATION.md) and [CLAUDE.md](../../CLAUDE.md).

## Source of truth

Read [current state and completion](../../doc/src/content/docs/architecture/current-state.mdx), [current build path](../../candidates/README.md), [manufacturing handoff](../../manufacturing/README.md) and [before-programming checklist](../../firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md).

The adopted path is zudo-pd P15 r1 plus the two existing Board Ls. `boards/board-p/` is the historical as-ordered lamp Board P, neither P15 nor PD20 r3. P15 source stays in zudo-pd; `boards/p15-r1-reference.json` is the consumer record. A matching reference hash is not electrical or per-unit acceptance, and permission here does not authorize writing the sibling.

Retain RS1 = 200 mOhm and `CTRL_FULL_CCR` = 2407; 250 mOhm/3200 are not selected. Read `firmware/board-l/target/OPEN-PRODUCT-DECISIONS.md` before choosing the bench image's behavior. Target build receipts remain UNFLASHED BENCH CANDIDATE until actual programming evidence exists. P15 NVM acceptance, Board L inspection, power/thermal/NTC checks and enclosure printing/fit are physical work, not cloud test results.

The source records #149/PR #150 and PR #152 as completed limited handoffs; refresh their actual state rather than repeating them. Physical #34/#35/#52 and the unadopted HUSB238 alternative #145 retain their own scope. Do not open a new routing campaign simply because this policy supports parallel work.

## Proposed lanes (none dispatched)

| Key / outcome | Environment and model | Dependencies / acceptance |
| --- | --- | --- |
| L-0: inventory latest issues, decisions, handoff artifacts, existing sessions and shared resources | Cloud manager + smallest adequate read-only child | First; do not duplicate completed handoffs or owner questions |
| L-1: verify pinned P15 owner/consumer and order-review artifact identities | Cloud fixed-command worker and scripts | Use `scripts/checks/verify-p15-reference.py` with an exact authorized zudo-pd checkout; missing historical STEP blocks full replay, not unrelated work; no supplier submission/order |
| L-2: decide any still-open firmware/bring-up design question | Fable/Astra for hard electrical/state decisions; manager presents genuine owner choices | Keep approved current/safety behavior; do not choose noise/gamma/latch/tuning for the owner implicitly |
| L-3: implement accepted firmware/check/tooling corrections | Isolated cloud child, suitable bounded implementation model | L-2 where relevant; target/host tests and receipt reproducibility; no flashing, option-byte writes or energization |
| L-4: bounded native/CAD/enclosure verification or evidence preparation | Existing Actions when appropriate; otherwise measured cloud VM, scripts and small coordinator | Preserve per-tool pins, source-bound geometry and physical unknowns; shared guards and complete deadlines |
| L-5: review, integration, documentation and owner handoff | Independent reviewer and single integrator | Update the existing current-state owner; distinguish built, flashed, measured, ordered and qualified |

Reuse `.github/workflows/component-spec-skills.yml`, `firmware-host-tests.yml`, `pr-checks.yml` and `main-deploy.yml` as their actual scopes allow. They are not OSC routing workflows. Read current package scripts, component validators and firmware Makefiles before constructing commands. Preserve generated component pages and previews; edit their sources only.

## Campaign control and holds

Record actual manager/dispatcher/session IDs, model selectors, exact source and P15 pins, allowed writes, shared account allocations/CI reserve, measured VM limits, finite budgets, evidence access and next steps under `campaigns/<campaign-id>/`. No fixed provider VM spec or concurrency limit is assumed. Missing cloud-accessible evidence requires a narrowly scoped transfer/local task, not a full rerun. Use the task brief; keep independent work moving while hardware gates remain held.

For the current matching DNS incident, follow ORCHESTRATION: defer network repair/polling and continue available work, without labelling unrun checks passed or assuming this repo has failed. Existing main pushes touching `circuit/**` or `CLAUDE.md` can trigger the normal documentation build/deploy when credential gates permit it. No hosting configuration or separate deployment is authorized by this runbook.

## Rollout validation boundary

Only operating Markdown and agent entry links change. Circuit/firmware/CI/tool pins and generated outputs remain untouched. The original CLAUDE content was hash-checked and preserved before adding the entry. Full package/native/firmware/build tests were NOT RUN in this rollout host (pnpm absent, Node 22, direct GitHub DNS unavailable). Text/scope checks are not hardware acceptance.
