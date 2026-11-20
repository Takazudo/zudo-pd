# Moya + Codex Cloud: zudo-pd development workflow

Repository-owned operating procedure, 2026-11-16 JST. Use this workflow for a new
task or an ongoing campaign in `Takazudo/zudo-pd`. All required operating steps,
templates and prompts are maintained here; opening the OSC repository is not a
startup, dispatch, review or recovery requirement.

## Start here

| Local entry | Responsibility |
| --- | --- |
| [AGENTS.md](../../AGENTS.md), [CLAUDE.md](../../CLAUDE.md), [WORKFLOW.md](../WORKFLOW.md) | Repository instructions, hardware/source ownership, evidence and required checks |
| [ORCHESTRATION.md](../ORCHESTRATION.md) | Role/model preferences, resource admission, authority, storage, failures and integration policy |
| This guide | The manager's repeatable start -> assign -> collect -> review -> integrate -> resume procedure |
| [Current plan](current-plan.md) and the selected tracker | Which accepted work is next, its dependencies and current decisions |
| [Campaign/checkpoint template](../templates/orchestration-campaign.md) | Manager-owned queue, allocations, live attempts, decisions and restart record |
| [Task/result/review template](../templates/orchestration-task.md) | One worker's bounded brief, returned evidence and independent review/integration record |

At a new campaign's kickoff, copy the campaign template to
`circuit/orchestration/campaigns/<campaign-id>/plan.md` and the task template to
`circuit/orchestration/campaigns/<campaign-id>/<task-id>.md`. Fill the brief before
admission. Templates are unpublished working records; do not create empty live
campaigns just to populate the tree. A small task can use one tracker and one worker;
larger work uses an epic with independently completable children.

Moya/Codex launch controls and selected models must be observed in the actual clients.
An instruction naming a model is not proof of selection. This guide is an operating
procedure, not an installed scheduler. The current PD/LED consolidation is the
[local application example](#pdled-consolidation-example); its C1/C2 task names do
not define every future campaign.

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
actual selections, or `unknown`. Routine coordination can proceed while an
unrelated hard design decision awaits a suitable session. Workers return `NEEDS_DESIGN`
instead of changing circuit constraints or acceptance criteria.

## Startup and the first wave

1. Read the selected tracker, accepted plan, repository instructions and current
   checkpoint. Refresh this repository's heads, issues/PRs, existing live sessions
   and any sibling inputs explicitly required by the task. Reuse the tracker;
   reconcile any incumbent manager before taking ownership.
2. Record Moya's actual session URL/ID and campaign ID in the local campaign template
   copied to `circuit/orchestration/campaigns/<campaign-id>/plan.md`. Initially it is
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
   VM. Use measured allocations and preserve other campaigns' reserves.
5. Establish the next ready task's issue, scope and task brief, linking its parent when
   there is one. For a focused single-issue task, reuse that issue directly.
   Search before creating records. Moya owns the queue and shared allocation; children
   own their task result files. Native sub-issue relationships are optional capability,
   not a claim to make without successful API evidence.
6. Admit and dispatch one bounded task after its inputs, write ownership, checks,
   capability and resource budget are complete. Use the worker prompt in the local
   task template. Record the returned session/run ID immediately, collect the required
   result, obtain independent review and integrate in dependency order.

If the guest VM profile is available only after a session starts, first use an
explicitly bounded read-only inventory/profiling task. Before that launch, confirm
the available session slot, existing jobs, launch capability, numeric session limit
and finite deadline/usage budget. The worker reports the actual host/tools/model and
resource fingerprint; it performs no implementation or heavy computation. Complete
resource admission from that result before the substantive task starts. This uses
the existing authorized scope and does not permit fan-out against unknown headroom.

## Task states and the next action

| State | Required record / next action |
| --- | --- |
| `PLANNED` | Goal and dependencies recorded; manager completes the brief and prerequisites |
| `ADMITTED` | Inputs, authority, exclusive writes, budget, checks and reviewer confirmed; dispatcher may launch this attempt |
| `RUNNING` | Actual provider session/run ID recorded; collect completion events or bounded status results |
| `REVIEW_READY` | Final SHA and required result/evidence returned; an independent reviewer inspects those bytes |
| `INTEGRATED` | Authorized integration confirmed on the target branch, with required checks and a receipt; eligible delivery issue may close |
| `BLOCKED` / `NEEDS_DESIGN` | Name the missing prerequisite or decision, its owner and ready work that can continue |
| `FAILED` / `REJECTED` / `CANCELLED` | Retain the result and failure/stop evidence; any new admitted attempt gets a new ID |
| `UNKNOWN` | A launch or interrupted execution is unresolved; reconcile the original provider attempt before replacement |

Task execution state and adoption/release status are separate fields. A review request
for changes returns the task to its recorded implementation stage; retain the earlier
review and re-review the new final SHA. If merge authority is absent, a reviewed PR
stays `REVIEW_READY`, with integration explicitly pending. Closing an unrelated or
physical-evidence issue is never an automatic transition.

## Task contract and result

Use [the local bounded task template](../templates/orchestration-task.md). It includes
copyable worker and independent-review prompts. Each
assignment must contain its goal/non-goals, canonical tracker and parent/child links
when applicable, exact base commit,
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

The selected tracker is the progress/decision entry point. Child issues, when used, hold task-level development
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

Record the current user's request and existing applicable grants in the campaign:
implementation, issue maintenance, commit/push and merge scope. Reuse granted scope
without asking again. Repository/sibling writes, public cutover and hardware actions
are distinct; this reusable guide supplies procedure rather than a new grant.
Without merge authority, retain reviewed
PRs and delivery issues open for integration. With authority, complete eligible merges
after independent review, applicable policy and checks on the current head.

Existing `main-deploy.yml` can publish the site after an authorized main update. Record
that automatic outcome separately; do not introduce new hosting, alter secrets or
execute an additional release/deploy command just because a plan mentions a site.
Hardware orders, programming and energization need their own applicable scope and
acceptance; completing a software or documentation task does not establish them.

Close completed children after verified integration, then their parent when its full
acceptance is met. Keep other hardware obligations open according to their own
evidence. Stop when only owner/physical/platform gates remain and leave a
concrete handoff, rather than inventing unrelated work to keep a campaign busy.

## Manager start and resume prompts

For a new task, replace the tracker and accepted scope before use:

```text
Manage <accepted task scope> in Takazudo/zudo-pd as the single Moya manager,
using Codex Cloud for bounded implementation. The canonical tracker is <issue URL>.
Read its current body/comments, AGENTS.md, CLAUDE.md, circuit/WORKFLOW.md,
circuit/ORCHESTRATION.md, circuit/orchestration/moya-codex-cloud.md and
circuit/orchestration/current-plan.md. All operating templates are in this repo.

Reconcile existing campaigns, writers, PRs and live jobs first. Reuse the tracker
and actual grants. Copy the local campaign/checkpoint template only if no matching
campaign exists; record capabilities, measured allocations, ownership and next work.
Complete a local task brief for the first ready outcome before dispatch. Use its
worker prompt and independent-review prompt, record real session/run IDs, and
integrate accepted changes serially within the recorded authority. Maintain issues
and checkpoints. Return actual results, blockers and the next action.
```

For interruption recovery or manager takeover:

```text
Resume <campaign-id> in Takazudo/zudo-pd from
circuit/orchestration/campaigns/<campaign-id>/plan.md and <tracker URL>.
Read the local Moya + Codex Cloud workflow and repository instructions.
Reconcile the incumbent manager and record the new manager's acknowledgment.
Inspect current branches/SHAs, task results, retained artifact hashes and actual
provider jobs. Resolve UNKNOWN attempts before retrying or replacing workers.
Preserve unrelated diffs, unmerged work and the existing issue/PR/session mapping.
Refresh capacity and applicable grants, then resume only the recorded safe next
operation. Do not recreate a tracker, repeat a completed check without cause, or
assume a closed chat stopped its jobs. Report takeover and the next ready task.
```

## PD/LED consolidation example

The current application is [super epic #308](https://github.com/Takazudo/zudo-pd/issues/308)
and [the accepted consolidation plan](pd-led-unification.md). C0 recorded the plan;
the next implementation task is C1. These are planned task fields, not a launch
receipt or an admitted resource allocation:

| Task field | C1 application |
| --- | --- |
| Goal | Review the migration baseline and mappings before any LED import |
| Inputs | Refreshed PD and LED commits, their open issues/PRs, P15 owner/consumer records and the accepted plan |
| Allowed output | The campaign record, baseline manifest, path/route/fragment/evidence-ID tables, task/issue ownership map and bounded C2 brief |
| Dependency | Inspect PR #307's current state and reconcile overlapping writers; independent inventory may proceed |
| Scope boundary | Keep hardware, component evidence, native files, frozen packages and site routes unchanged during C1 |
| Completion | Manifest accounts for source/history/identity and required checks; independent reviewer accepts the mappings and C2 contract |
| Next | Dispatch the bounded C2 import only after the C1 review and its prerequisites |

Choose exclusive files, exact current SHAs, actual session/model controls and numeric
resource budgets at kickoff using the local templates. Keep #228 as the hardware
program and preserve the current plan's P15/PD15/PD20/LED evidence boundaries.

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
Use this repository's campaign and task templates; no OSC workflow reading is
required. Do not claim dispatch from a plan or assume another campaign's authority.

Require independent review and applicable checks on final integration bytes.
Keep shared writers serialized, preserve history and unresolved physical evidence,
checkpoint before interruptions, and report what is integrated, pending and blocked.
Continue ready in-scope work; leave review-ready PRs open unless merge has been
authorized for this campaign. No hardware orders, programming or energization.
```

## Optional provenance

The initial policy was adapted from `zudo-osc-hole-field`, inspected at
`85b2b489d6f47b34991e3d9b0d2e09991a458a97` in the earlier planning session.
That source is historical attribution. The maintained operating contract, templates,
PD-specific example and prompts are the local files linked above. Changes to another
repository's campaign, permissions, model selections, resource numbers or tool pins
do not silently update this workflow.
