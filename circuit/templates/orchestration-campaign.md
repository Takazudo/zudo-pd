# Campaign: `<campaign-id>`

Unpublished template. Copy to `circuit/orchestration/campaigns/<campaign-id>/plan.md`
when starting an accepted campaign. Read the repository-local procedure at
`circuit/orchestration/moya-codex-cloud.md`. Fill required fields before dispatch;
this template does not launch workers, allocate capacity or grant permissions.

The single manager owns this file and shared allocations. Workers write their own
`<task-id>.md` result records. Use repository-relative paths in completed records;
resolve all placeholder values and link the actual tracker, tasks and receipts.

## Control and accepted scope

| Field | Value |
| --- | --- |
| Campaign state / last updated | `PLANNED` / UNASSIGNED |
| Canonical tracker / accepted plan | UNASSIGNED |
| Goal and completion criteria | UNASSIGNED |
| Non-goals and protected source/evidence | UNASSIGNED |
| User request / applicable authorization record | UNASSIGNED |
| Implementation / issue maintenance / commit / push ownership | UNASSIGNED |
| Merge / deployment / sibling / physical action scope | UNASSIGNED; do not infer from another campaign |
| Single manager session URL/ID | UNASSIGNED |
| Dispatcher / integrator | UNASSIGNED |
| Independent reviewer assignment | UNASSIGNED |
| Previous manager / takeover acknowledgment | UNASSIGNED, or N/A with reason |
| Destination repo / target branch / observed SHA | UNASSIGNED |
| Declared sibling inputs / immutable commits | UNASSIGNED, or N/A with reason |

## Capabilities and finite allocation

- Observation time and evidence for launch controls, GitHub access, model selection
  and completion notifications:
- Requested model/effort versus actual selected model/effort; unknown fields:
- Account/pool limits, current other-work occupancy, numeric campaign ceiling and CI reserve:
- Allowed simultaneous worker sessions, jobs and heavy processes:
- Each actual VM/runner: CPU quota/affinity, RAM/cgroup/current headroom, safety reserve,
  swap/disk, tools and enforced lifetime; include child/container consumption:
- Setup, execution, validation, cleanup and transfer deadlines:
- Usage/spend ceiling, no-progress limit, retry limit and observation basis:
- Authorized artifact destinations, access, byte/retention/expiry limits:
- Shared writer/dispatcher allocation and any existing live-job conflicts:

If guest profiling needs a launched session, record a separate bounded read-only
bootstrap task: confirmed slot/occupancy, session limit, deadline/usage budget,
permitted observations and returned fingerprint. No implementation or heavy job is
admitted until that result completes the substantive task's resource prerequisites.

Unknown capacity is not unlimited. Fill the required admission fields in each task
before launch. A worktree does not add CPU/RAM. A non-applicable measurement can be
N/A with a reason; a missing required capability remains a blocker.

## Task queue and exclusive ownership

| Task / issue | Outcome / acceptance | Dependencies | State | Allowed files / writer | Branch / base SHA | Worker / reviewer | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UNASSIGNED | UNASSIGNED | UNASSIGNED | PLANNED | UNASSIGNED | UNASSIGNED | UNASSIGNED | Complete a bounded task brief |

Use the local task template for the full brief, worker prompt and review prompt.
States follow the local workflow: PLANNED, ADMITTED, RUNNING, REVIEW_READY,
INTEGRATED, BLOCKED, NEEDS_DESIGN, FAILED, REJECTED, CANCELLED or UNKNOWN.
Execution success and adoption/release status stay separate.

## Attempt and live-job ledger

| Task key / attempt ID | Provider session/run/job ID | Exact inputs / tool identity | Observed state / time | Result / artifact hashes | Resource owner / next check |
| --- | --- | --- | --- | --- | --- |
| UNASSIGNED | Not launched | UNASSIGNED | PLANNED | None | UNASSIGNED |

After an uncertain launch, reconcile this attempt before replacement. Keep failed and
interrupted rows; a retry gets a new attempt ID and its admission reason. The ledger
is not a distributed lock: one dispatcher owns the allocation.

## Decisions and blockers

| ID / task | Evidence and exact question | Recommendation / decision | Decision owner / authorization | Ready work that can continue |
| --- | --- | --- | --- | --- |
| UNASSIGNED | UNASSIGNED | UNASSIGNED | UNASSIGNED | UNASSIGNED |

Agent recommendations are not owner approvals. Link actual adopted decisions and
retain unresolved, physical and access requirements with their next owner/action.

## Integration receipts

| Task | Reviewed SHA / reviewer record | Target base / integration SHA / PR | Checks and deployment outcome | Issue disposition |
| --- | --- | --- | --- | --- |
| UNASSIGNED | Not reviewed | Not integrated | NOT RUN | Open |

Close eligible children after verified integration, then their parent after its full
acceptance. Keep independent product/bench issues under their own evidence criteria.

## Latest durable checkpoint and takeover

- Checkpoint time; manager session; campaign revision:
- Current target/working SHAs and task/issue/PR/branch/session mapping:
- Live or UNKNOWN jobs queried; terminal/stop evidence and retained allocations:
- Accepted results and candidate bytes; artifact hashes, access and expiry:
- Last completed checks; failures and NOT RUN checks with reasons:
- Decisions/blockers; exact next safe operation and assigned owner:
- Protected unrelated diffs; owned unmerged branches/worktrees and recovery artifacts:
- Disposable resources cleaned; unresolved cleanup; released capacity:
- Checkout state; receiver/new-manager acknowledgment and next check:

Before resume, read this record, query actual provider state and verify the retained
inputs/results. Reuse the existing tracker and workers where valid. A progress note
without the necessary result bytes is not a recoverable checkpoint.
