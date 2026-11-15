# Moya + Codex Cloud: PD/LED consolidation handoff

Owner-selected next execution route, recorded 2026-11-16 JST.
Read [ORCHESTRATION.md](../ORCHESTRATION.md), [WORKFLOW.md](../WORKFLOW.md),
[CLAUDE.md](../../CLAUDE.md), [the consolidation plan](pd-led-unification.md) and
[super epic #308](https://github.com/Takazudo/zudo-pd/issues/308). This supplement applies the existing runbook to the
accepted consolidation scope; it does not start a session or install a scheduler.

## Reference and adaptation

Adapted from `zudo-osc-hole-field` at
`85b2b489d6f47b34991e3d9b0d2e09991a458a97`:
[orchestration policy](https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/ORCHESTRATION.md),
[task template](https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/templates/orchestration-task.md),
[campaign example](https://github.com/Takazudo/zudo-osc-hole-field/blob/85b2b489d6f47b34991e3d9b0d2e09991a458a97/circuit/orchestration/campaigns/osc-stack-20261114/plan.md)
and [coordination format](https://github.com/Takazudo/zudo-osc-hole-field/issues/288).

Reuse the division of responsibilities, bounded tasks, independent review, durable
handoff and serialized integration. OSC's inspected live campaign used Claude Code
Cloud; its CPU/RAM/session limits, native admissions, merge grants, tool pins and
historical holds do not transfer here. Moya/Codex capabilities must be observed in
the actual clients. An instruction naming a model is not proof of model selection.

## Roles

| Role | Responsibility |
| --- | --- |
| Moya: one active manager | Maintain the epic, accepted plan, task graph, decisions, account allocation, dispatch ledger, blockers and integration order |
| Codex Cloud implementer | Own one coherent bounded task in its assigned branch/workspace, implement and run applicable checks, return a revision-bound result |
| Independent reviewer | Inspect the actual diff and evidence against the task contract; record findings independently of the implementer's completion claim |
| Single integrator | Reconcile current base, adopt accepted changes serially, verify the integration revision, maintain issue/PR links and report deployment separately |
| Scripts / existing Actions | Run deterministic checks and supported result collection within the admitted resource budget |

Moya may be the integrator if its actual tools and owner-granted scope support that
role. Otherwise name one integrator explicitly. Normally use two management levels.
Keep one topic with one worker across follow-ups. Parallelize disjoint outcomes only;
do not assign concurrent writers to shared evidence, package files or generated output.

Follow the existing model preferences: confirmed Astra/Fable for hard new design or
validation-policy decisions, Sol or another demonstrated adequate model for substantial
implementation, and smaller adequate models for fixed work. Record requested and
actual selections, or `unknown`. Routine migration coordination can proceed while an
unrelated hard design decision awaits a suitable session. Workers return `NEEDS_DESIGN`
instead of changing circuit constraints or acceptance criteria.

## Startup and the first wave

1. Read the epic, accepted plan, repository instructions and current checkpoint. Refresh
   both repositories' heads, issues/PRs and existing live sessions. Reuse the tracker;
   reconcile any incumbent manager before taking ownership.
2. Record Moya's actual session URL/ID and campaign ID under
   `circuit/orchestration/campaigns/<campaign-id>/plan.md`. Initially the campaign is
   `PLANNED`; none of the sessions, branches or resource reservations in a proposal
   should be presented as existing.
3. Confirm how this client launches Codex Cloud work, returns session/run IDs, selects
   models, exposes GitHub permissions and reports completion. If direct launch is not
   available, prepare the exact task prompt for the user to start in Codex Cloud and
   record the returned session before calling it dispatched. Do not invent a CLI/API.
4. Observe shared-account occupancy, available session/job limits and VM fingerprints.
   Set finite numeric task/session limits, CI reserve, deadlines and retry budgets.
   Unknown headroom prevents unbounded fan-out, not read-only inventory. Worktrees and
   subagents in one VM share CPU/RAM; keep at most one admitted heavy job per unprofiled
   VM. Do not copy OSC's allocation numbers or consume another campaign's reserve.
5. Establish C1's child issue, scope and task brief, with body links back to the epic.
   Search before creating records. Moya owns the queue and shared allocation; children
   own their task result files. Native sub-issue relationships are optional capability,
   not a claim to make without successful API evidence.
6. Dispatch the bounded C1 baseline/mapping task. Its first outputs are the manifest,
   reviewed path/ID/route mappings, conflict disposition for #307 and a C2 import brief.
   Proceed through the plan's dependency order after review, rather than handing the
   whole migration to one context-free worker.

## Task contract and result

Use [the existing bounded task template](../templates/orchestration-task.md). Each
assignment must contain its goal/non-goals, child issue and epic, exact base commit,
input identities, dependencies, allowed files, exclusive branch/workspace, tools,
commands, acceptance criteria, reviewer/integrator, artifact policy, finite deadline,
retry/stop conditions and granted actions. Keep commit/push ownership explicit;
absent another recorded allocation, the manager/integrator owns remote integration.

Derive a stable task key from input/program/tool identities and parameters, and a
unique attempt ID for each launch. Record the provider session/run ID immediately.
After an uncertain response, reconcile that attempt before launching a replacement.

The worker returns: inspected base and final SHA, changed files and purpose, commands
and actual results, checks `NOT RUN` with reasons, artifact locations/hashes, open
findings, PR/branch/session IDs, cleanup state and the next safe action. A result is
`REVIEW_READY` only when evidence is complete; a zero exit does not mean `INTEGRATED`.

The reviewer checks the same final bytes. The integrator then rechecks base drift,
regenerates owned outputs and runs required checks on the actual integration revision.
Do not merge stale results or resolve CAD/evidence conflicts by accepting arbitrary
text. Preserve failed cases and unresolved evidence instead of weakening gates.

## Progress, interruption and coordination

The epic is the progress/decision entry point. Child issues hold task-level development
notes; campaign files hold reproducible inputs and receipts. Record meaningful changes,
review/verification results, blockers and pauses rather than routine polling transcripts.

Use this comment shape when a cross-task update or decision is useful:

```text
Type: RESULT | QUESTION | APPROVAL NEEDED | LOCAL WORK | BLOCKED
ID: <campaign/task/request ID>; owner: <agent/session>
Issue / PR / branch / inspected SHA:
Evidence and result:
Decision needed or accepted decision reference:
Parallel work that can continue:
Next action / owner:
```

An agent's recommendation is not user approval. Reuse already granted scope without
asking again. Escalate only a concrete new decision, missing capability or action
outside that scope; keep independent work moving.

Prefer completion events or bounded non-LLM monitoring with backoff. If durable
monitoring is unavailable, leave run IDs and the next check; do not promise that a
closed chat continues watching. Retry at most once for a confirmed transient failure
after proving the prior attempt stopped. Deterministic failure, stale inputs and
unsupported environments require a changed plan, not identical retries.

Before interruption, persist task/issue/PR/branch/session mappings, live jobs, accepted
inputs and outputs, hashes, review state, failures, capacity and exact next action.
Preserve recovery-critical bytes in an authorized durable destination before releasing
the VM. Local-only STEP and private vendor-source restrictions still apply. On resume,
read the checkpoint, query live attempts and verify hashes before starting anything.

At handoff, classify all diffs and owned resources. Keep unmerged branches/PRs, needed
worktrees and recovery artifacts. Remove only verified disposable campaign resources;
never discard unrelated work. Return a clean safe checkout where possible, or report
the exact retained diff and ownership. Record unresolved cleanup instead of claiming
completion. The manager verifies safety and permission before retrying denied cleanup.

## Integration and scope

The user has authorized this session's epic and planning-document updates. The next
campaign's kickoff records its own implementation, issue-maintenance, commit/push and
merge scope. Repository/sibling writes, public cutover and hardware actions are distinct;
the imported OSC runbook does not grant them. Without merge authority, retain reviewed
PRs and delivery issues open for integration. With authority, complete eligible merges
after independent review, applicable policy and checks on the current head.

Existing `main-deploy.yml` can publish the site after an authorized main update. Record
that automatic outcome separately; do not introduce new hosting, alter secrets or
execute an additional release/deploy command just because a plan mentions a site.
Do not order, program, energize or qualify hardware through the migration task.

Close completed children after verified integration, then the consolidation epic when
its acceptance is met. Keep #228 and other hardware obligations open according to
their own evidence. Stop when only owner/physical/platform gates remain and leave a
concrete handoff, rather than inventing unrelated work to keep a campaign busy.

## Kickoff prompt

The user can give the following to Moya when starting implementation. It is a future
execution brief, not a claim that this planning session has launched that work.

```text
Use the PD/LED consolidation super epic linked from Takazudo/zudo-pd/readme.md
as the canonical tracker. Read its current body/comments, AGENTS.md, CLAUDE.md,
circuit/WORKFLOW.md, circuit/ORCHESTRATION.md,
circuit/orchestration/pd-led-unification.md and
circuit/orchestration/moya-codex-cloud.md.

You are the single Moya manager; use Codex Cloud for bounded implementation.
Carry out the accepted repository/documentation consolidation in dependency order.
First refresh source heads, existing PRs/issues and live workers, establish/reuse
child tracking, and complete C1's baseline/manifest/mapping review before C2 import.
Preserve PD20 PR #307's independent work and the fixed P15/evidence identities.

Maintain the epic and child issues, record decisions and verification, and create
reviewable commits/PRs within the implementation scope. Confirm actual launch/model
controls, resource limits and granted integration actions. If you cannot launch a
worker directly, return its exact prompt and record the actual session after launch.
Do not claim dispatch from a plan or assume another campaign's merge authority.

Require independent review and applicable checks on final integration bytes.
Keep shared writers serialized, preserve history and unresolved physical evidence,
checkpoint before interruptions, and report what is integrated, pending and blocked.
Continue ready in-scope work; leave review-ready PRs open unless merge has been
authorized for this campaign. No hardware orders, programming or energization.
```
