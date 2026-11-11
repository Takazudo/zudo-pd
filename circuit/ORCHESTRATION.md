# Cloud-first circuit development orchestration

Owner-directed policy, 2026-11-12. Adapted from zudo-osc-hole-field PR #329 (merge `ebfbc0940d2af6bc199405d4d5dbef8950a6bfa5`), not its PCB state, task IDs, tool pins or execution permissions. Read the root agent instructions and applicable component/evidence workflow first. [Current mapping](orchestration/current-plan.md) owns the repository-specific starting points; use the [task brief](templates/orchestration-task.md) for admitted work.

This is a runbook, not an installed scheduler. It neither starts a campaign nor authorizes new hardware actions. Existing design decisions, immutable evidence, local-only storage, native gates and publication restrictions remain authoritative.

## 1. Manager and model roles

Use one active top-level manager per campaign: Claude Code Cloud Project or ChatGPT Dots. Record the actual session ID and reconcile an incumbent before takeover. Use supported child-session facilities only; discover capabilities rather than inventing APIs. If children are unavailable, work sequentially and say so.

| Work | Preferred role/model | Boundary |
| --- | --- | --- |
| Hard circuit, architecture, protection or validation-policy decision | Fable / Astra | Confirm actual model selection; otherwise hold that decision, not unrelated work |
| Substantial implementation or child-manager judgment | Opus / Sol; escalate hard decisions | Own a coherent deliverable and explicit write scope |
| Fixed-design implementation | Sonnet / Luna / Terra, when demonstrated adequate | No independent design or acceptance changes |
| Fixed Actions dispatch and result collection | Smallest adequate available model, e.g. Haiku / Luna | One dispatcher per allocated pool, not one manager per job |
| Routing, simulation, refill, DRC, normal waiting and metrics | Programs/workflows, no LLM | Return structured terminal results |

These are owner preferences, not availability or benchmark guarantees. Record requested versus actually selected model and effort when exposed; an instruction asking for a model is not a selector. Opaque routing is `unknown`. A powerful manager should not spend reasoning turns watching healthy jobs, even through a cheap polling subagent.

## 2. Bounded delegation and authority

Split by independent outcome, write ownership, resource profile and recovery boundary, not by individual command or net. Normally keep two management levels. Reuse a child for its topic. Each child receives an exact base, task/issue, inputs, dependencies, allowed files, budget, checks and return contract. Follow repository commit/push ownership; absent an explicit allocation, the manager owns push and integration.

Implementation, workflow dispatch, candidate transfer, canonical adoption, merge, release, deployment, supplier contact, programming, energization and ordering are separate authorities. Use the current owner's scoped request; do not ask again for already granted routine work, but do not infer a hardware action or sibling-repository write from a runbook. Preserve owner holds and genuine approval controls. Grok Bot / Cursor is excluded from the default execution routes by owner operational choice.

## 3. Shared resources before fan-out

Prefer existing GitHub Actions for deterministic work that fits the complete runtime and tooling requirements. Use cloud child VMs for implementation and justified computation, not automatically whenever Actions is busy. Compare queueing, setup, transfer, interruption risk and model usage before adding a VM; never duplicate an in-flight attempt.

Account/pool capacity is shared across zudo-osc-hole-field, zudo-pd, zudo-led-lamp, zudo-led-block and other work. Each repository manager must reconcile peer allocations rather than claiming the whole account. Keep one agreed dispatcher per pool allocation. Reserve ordinary CI and integration capacity before allocating compute; count preparation, aggregation, artifact collection and automatic push/PR CI too. A matrix `max-parallel` is not an account-wide cap. Unknown quota is not unlimited; do not flood the service to discover it.

Before launch record numeric session/job limits, occupancy, CI reserve, memory/CPU allocations, time/usage ceilings and their observed basis. A Markdown allocation is not a distributed lock: use a single dispatcher unless a real atomic lease is implemented. Unknown shared headroom blocks fan-out, not read-only planning.

A worktree, clone, terminal or subagent does not add CPU/RAM. Count all processes in a VM together unless isolation is verified. Windows and WSL share physical-host resources. Fingerprint actual CPU affinity/quota, cgroup limits/current usage, available memory, swap, disk, tools and lifetime. Do not equate RAM total, cgroup ceiling and immediately available memory. Include child/container peaks and OS/finalization reserve. Default to at most one admitted heavy job per unprofiled VM; even that needs a bounded estimate and the existing guard.

Full setup + computation + verification + cleanup + upload must fit the enforced deadline. A single memory-heavy job cannot pool RAM from several small VMs. Stage chains consume the previous accepted candidate; do not parallelize dependent stages on stale predecessors. Independent candidate trials or proven-independent fixtures may run concurrently, but final whole-design acceptance is still required.

## 4. Isolated execution and recovery

Use separate branches/workspaces and unique cache/output paths for independent writers. Freeze input revisions during expensive work. Preserve source ownership and regenerate generated files; never merge PCB text or evidence hashes merely to resolve a conflict. Sibling inputs require immutable source/consumer pins and explicit handoff.

Use a stable task key (input/program/tool hashes plus normalized parameters) and a unique attempt ID. Record provider run/session IDs immediately. After an uncertain launch, query the original attempt before retrying. A timeout or expired chat does not prove its process stopped.

Checkpoint expensive recoverable boundaries with the actual candidate, input/context, progress, logs, tool identity, hashes and next supported operation. A progress JSON without its bytes is not recoverable. Verify authorized destination access, transfer hashes, retention and expiry; do not upload local-only, restricted or private data under a generic artifact rule. Reuse completed evidence only when all bindings and applicability hold. Never rerun expensive work merely because a fresh VM lacks its cache.

## 5. Waiting, telemetry and failures

Use actual completion events or bounded non-LLM status monitoring with backoff. Where durable monitoring is unavailable, leave a concrete next-check handoff; do not claim a sleeping chat or detached process will survive. Keep full logs in permitted artifacts and return compact phase timings, aggregate peak memory, progress, gates, hashes and failure classification. Model usage is `unknown` unless observed.

Set finite runtime, retry and no-progress limits. Default transient retry allowance is at most one, after confirming the old attempt stopped and recording the transient cause. Deterministic rejection, no improvement, stale hashes and unsupported environments are not transient. Preserve first failures. Exit 137 alone is not proof of OOM; distinguish signals, deadlines and measured memory events. Clean up only verified owned processes/containers, never unrelated work.

Optimize through equivalent reuse, proven early rejection and bounded restart, not by deleting validation passes, relaxing rules, changing parts or weakening negative controls. A small executor returns `NEEDS_DESIGN` when its fixed contract fails rather than improvising a new circuit.

## 6. Verification and serialized integration

Select this repository's actual native oracle, compiler, numerical and CAD pins from its current source. Do not copy OSC's KiCad version, commands, time limits or acceptance counts. Keep preview renderers separate from native engineering tools.

Run applicable baseline/focused/generation/native checks and independent review bound to the final bytes. The sole integrator rechecks the current base, applies accepted source/candidate changes, regenerates owned outputs and verifies the integration revision. A child's completion message, zero exit, DRC pass or green CI is not hardware qualification. Keep digital, programmed, received, measured, order-review and manufacturing-release states separate.

Merge when the current request authorizes it and applicable review/check/policy requirements hold. Otherwise keep a useful draft. Do not change repository protections, falsify statuses or treat a one-off documentation exception as permission to merge unverified circuit changes. Inspect existing automatic site deployment effects before an authorized push/merge; do not enable hosting or execute separate deployment/release commands without authority.

## 7. Current DNS incident: defer, do not repair

For this 2026-11-12 kickoff, the owner prioritizes development over the previously observed Ubuntu APT mirror DNS failure during browser dependency setup in OSC run `43043788239` (apt exit 100). This is a presumed transient external incident, not verified recovery or proof these repositories have the same failure.

If that same signature affects work here, record infrastructure-blocked / `NOT RUN`; do not poll, manually retry, open repair work, change mirrors/runners/pins/timeouts or revert documentation just to turn the badge green. Do not require a green main badge to begin independent work or repeatedly ask the owner about this accepted incident. Continue available focused checks and other tasks; defer only the operation that needs unavailable access. Existing automatic CI can run normally.

This is an incident-specific priority decision, not a permanent CI waiver. New unexplained failures and genuine regressions need their own disposition; native/adoption evidence remains mandatory. The owner requested this documentation-only rollout directly on main; that does not create standing direct-push or merge permission for future implementations.

## 8. Local escalation, backlog and continuation

Prefer cloud completion. When measured resources, native OS/hardware evidence, retained files or runtime require Windows/WSL/macOS, record the smallest local scope, budget and return artifact. Use preconnected environments only within existing authorization; request missing access/scope when needed. A desktop connection does not prove WSL access. Keep independent cloud work moving.

Reuse actual trackers before creating more. Classify open PRs/issues as ready, implementation/review pending, superseded, rejected evidence, owner hold, or evidence/environment blocked. Do not mass-close by age, green CI or an obsolete headline. Close only verified completed scope or explicitly documented safe duplicates/retirements; preserve unique evidence, stacked dependencies and held branches.

For an owner-authorized continuous campaign, repeat inspect → plan → implement → independently review → verify → integrate when authorized → resweep. Do not stop at the first PR, but do not invent work when only physical/owner gates remain. Persist the task/issue/branch/session mapping, decisions, blockers and next action before interruption. Keep paused worktrees and recovery artifacts; remove only this campaign's verified disposable resources, and leave the main checkout clean without discarding unrelated changes.
