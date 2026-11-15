# Bounded orchestration task

Copy under `circuit/orchestration/campaigns/<campaign-id>/<task-id>.md` only when a campaign starts. Unknown prerequisites do not mean admitted. Use the current request and repository rules, not this blank template, as authority.

The manager owns admission and integration; the worker fills its result; an independent
reviewer fills the review record. Use `circuit/orchestration/moya-codex-cloud.md` and
the local campaign template. No sibling repository's workflow is required.

- Task state: `PLANNED`
- Separate adoption/release status: not adopted / not released
- Attempt history: retain each attempt ID and first failure; never overwrite a failed
  attempt when retrying. UNKNOWN attempts must be reconciled before replacement.
- Use N/A with a reason for genuinely inapplicable fields. Missing required evidence
  remains unknown or blocked; N/A cannot waive a gate.

## Before admission

- Campaign/task/attempt IDs; stable input/program/parameter task key:
- Existing tracker/issue; manager, child, sole dispatcher and integrator IDs:
- Goal, non-goals, dependencies, acceptance criteria and independent reviewer:
- Source/base revision, board/product variant, inputs/context and SHA256 manifest:
- Actual tools/image/compiler pins; requested/selected model and effort evidence:
- Branch/workspace; unique cache/output; allowed writes; immutable/local-only paths:
- Current jobs/peer-repository allocation checked; no duplicate attempt:
- Actual host/VM identity, CPU quota/affinity, RAM/cgroup headroom, swap/disk:
- Numeric account allocation, other occupancy, CI reserve and child allocation:
- Setup/compute/validation/cleanup/upload limits; memory including children; usage/no-progress/retry limits:
- Exact supported command/workflow ref and inputs; current authorization:
- Authorized artifact destination, allowlist, byte/retention limits and access:
- Completion event or bounded non-LLM monitor; supported checkpoint/resume boundary:
- Stop, owned cleanup and uncertain-launch reconciliation procedure:

## Result and handoff

- Provider run/job/session ID, attempt, exact source/tool/output identities:
- Execution outcome separately from adoption/release status; first failure retained:
- Setup/search/simulation/refill/DRC/audit/wait timings; aggregate peak memory:
- Model usage/credits when observed, otherwise unknown:
- Changes, candidate/evidence/log locations, complete manifest and transfer verification:
- Actual checks, limits and NOT RUN items; independent final-byte review:
- Current-base applicability; integration commit/PR and post-integration results:
- Remaining owner/physical/access decisions; next safe operation:
- Owned resource cleanup, released allocation, evidence retention responsibility:

Never fabricate an API, model selection, measurement, reviewer or successful check. No automatic rule relaxation, canonical promotion, programming, ordering or deployment.

## Independent review and integration record

- Reviewer identity/session, independent of the implementer:
- Reviewed base and exact final SHA / artifact hashes:
- Contract, scope, source/evidence preservation and check findings:
- Verdict: accepted for integration / changes required / blocked; reasons:
- Finding IDs, resolutions and re-reviewed final SHA:
- Integrator, current target base, applicable merge authority:
- Base-drift reconciliation and actual integration commit / PR:
- Required check commands, exit/results and current-head CI receipts:
- Automatic deployment outcome separately from merge, when applicable:
- Child/parent issue disposition, retained resources and next owner/action:

A result can become REVIEW_READY before integration. INTEGRATED requires the target
branch receipt and applicable checks, not only a successful worker or review message.

## Worker prompt

Fill the task brief above and replace all prompt placeholders before dispatch:

```text
Implement task <task-id> for <tracker/child issue URL> in Takazudo/zudo-pd.
Your complete brief is <repository-relative task file> at base <exact SHA>.
Read it, AGENTS.md, CLAUDE.md, circuit/WORKFLOW.md,
circuit/ORCHESTRATION.md and circuit/orchestration/moya-codex-cloud.md.

Verify the assigned base, dependencies and allowed writes before editing. Use the
assigned isolated workspace and branch, obey commit/push ownership and the admitted
resource/deadline/retry budget. Run the specified baseline and completion checks.
Preserve source ownership and hardware/evidence gates. Return NEEDS_DESIGN for a
new design or validation-policy decision; do not silently broaden the task.

Write the result into your task record: final SHA, changed files, actual commands
and outcomes, NOT RUN items, artifacts/hashes, failures, live-job/cleanup state and
next safe action. Update the assigned issue within your grant. Do not self-approve
independent review, merge without authority, or change the manager's allocation.
```

## Independent-review prompt

```text
Independently review task <task-id> in Takazudo/zudo-pd; you are not its implementer.
Read <task file>, <tracker/child issue URL>, the local workflow and repository rules.
Inspect the actual diff from <base SHA> to <final SHA> and its retained artifacts.
Check scope, accepted decisions, source/evidence preservation, generated ownership,
test applicability and actual results. Verify that unavailable evidence is explicit.

Record the inspected SHA, findings, severity, required resolution and verdict in
the task's review section or assigned review record. Give an actionable changes-
required/blocked result when needed. Do not treat the worker's report as proof,
edit implementation or merge unless separately assigned. A changed final SHA needs
reconciliation and re-review of affected findings before integration.
```
