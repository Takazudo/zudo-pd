# zudo-pd orchestration mapping

## Accepted next campaign: PD/LED consolidation

Updated 2026-11-16 JST (2026-11-15 UTC). The owner selected **Moya + Codex Cloud**
for the next implementation session. The [super epic #308](https://github.com/Takazudo/zudo-pd/issues/308),
[accepted consolidation plan](pd-led-unification.md) and
[execution handoff](moya-codex-cloud.md) are its entry points.
This update records the plan; it does not launch workers or migrate LED/source/docs.

| Control / starting point | Observed state / next action |
| --- | --- |
| Destination | `zudo-pd/main` inspected at `b377136d96f738a803a5dc5e8416402450dceeb7`, through #306; refresh before implementation |
| LED input | `zudo-led-lamp/main` inspected at `88cb17409cf16a0391e8eadf0ad8a43d60a37356`; preserve original history and source identities |
| Manager / implementation environment | Intended single manager Moya; Codex Cloud implements bounded tasks; actual sessions and launch controls not yet assigned |
| First deliverable | C1 migration baseline, path/route/fragment/evidence-ID mapping, child issue and writer allocation, then a reviewed C2 import brief |
| In-flight circuit work | #307 remains open at `9312dc627df2de22d1ac44a3a05fbcb207665b3e`; inspect its latest disposition before overlapping moves or evidence/configuration changes |
| Existing hardware tracking | #228 remains the hardware completion owner; #235 and #279 retain their own PD20 acceptance scope; #210 retains framework-bridge parity obligations |
| Resource / model / integration allocation | Unassigned for this campaign; observe capacity, reserve CI and record actual selections and granted actions at kickoff |
| Target | One repository, one site, one Components catalog; Project / Shared P15 / PD15 / PD20 / LED Lamp / Components |

Migration completion and hardware qualification are separate. Preserve the dated
order/received/programmed/measured records and the fixed P15 package. The current
documentation update is not a hardware decision, a public-site cutover or standing
authority to merge future migration work. See the plan's C0-C6 sequence and use
the existing bounded task template for dispatch.

## Historical initialization (2026-11-12)

The following mapping is retained as the earlier orchestration baseline. It is not
the current consolidation queue or evidence that old holds remain unresolved.
Re-triage engineering work against current source and newer decisions.

Policy date: 2026-11-12 JST (2026-11-11 UTC), committed in `0803524786d9eaf137fa61f33b15aaf51a354811` on parent main `28451308655b36ad2b7afbb4487b195c432bbf7e` (PR #240 merged). Last re-inspected main: `db49cfea495e86ceddb280c675fb1f7dafa1b791` (PR #247 merged) on 2026-11-11 UTC. This is an initial mapping, not a launch receipt or fresh hardware check. Refresh current source/issues before execution. Apply [ORCHESTRATION.md](../ORCHESTRATION.md), [WORKFLOW.md](../WORKFLOW.md) and [CLAUDE.md](../../CLAUDE.md).

## Authoritative entry points and boundaries

- [Current state](../../doc/src/content/docs/project/current-state.md) owns dated artifact/order/programming/measurement status; [release readiness](../../doc/src/content/docs/architecture/release-readiness.md) owns acceptance. Read the [prototype-order ledger](../../manufacturing/prototype-order-readiness.md) and tracker [#228](https://github.com/Takazudo/zudo-pd/issues/228) plus current comments. Do not reinterpret an older paragraph as a fresh main receipt.
- Keep three distinct streams: shared P15 r1 input; PD15 = `board-p15 + board-b`; PD20 = `board-p + board-b20-draft` (20 V r3). Historical root/Board A/15 V r2 and received S3 Board B are not current development hardware.
- P15 is the source owner for the lamp consumer. Inspect `boards/board-p15/shared-reference.json` and the consumer pin; do not silently repin the sibling or treat cross-repository availability as write authority.
- The fixed `manufacturing/releases/corner-support-review/` packet is revision-bound, not arbitrary HEAD. Missing original local-only STEP prevents its full replay; do not regenerate locks to claim success, upload restricted assembled STEP previews, use Git LFS or add backup output folders.
- Current-state records describe digital/native/layout/export progress but retain PD20 startup/current/NVM and physical holds. In particular, PD20 intent JSON is not a program-ready binary. P15's prototype protection residual is not a new protection approval. Read the actual gate owners before selecting work.

## Historical proposed engineering lanes (none dispatched by this record)

| Key / outcome | Environment and model | Dependency / acceptance boundary |
| --- | --- | --- |
| PD-0: refresh #228, open PRs/issues, source/evidence index, actual model/host controls and shared capacity | Cloud manager; adequate small child for read-only inventory | First; reconcile existing local/cloud work and reserve account-wide CI capacity |
| PD-1: reconcile P15 source, fixed package and lamp handoff identities | Cloud; bounded implementation/collection model | Read-only sibling at explicit pin; package replay needs exact originals; no order, upload or per-unit programming |
| PD-2: diagnose remaining PD20 startup/protection/current and NVM decisions from retained evidence | Fable/Astra design; Opus/Sol for tools; scripts for fixed cases | Reuse #228/#230 where applicable; preserve adopted exceptions and failed cases; no invented NVM binary or measured rating |
| PD-3: implement a reviewed, bounded correction and evidence refresh | Isolated cloud child; Sonnet or appropriate capable model | PD-2 decision when needed; share spec/layout/publication writes only through the manager |
| PD-4: admitted native/simulation/CAD checks and collection | Existing Actions where suitable, otherwise fingerprinted cloud VM; small coordinator + programs | Exact input/tool bindings, complete deadline and storage fit; one heavy process per unprofiled VM; original-only replay may need scoped local access |
| PD-5: exact-byte review, variant-correct integration and current-state update | Independent reviewer and single integrator; reserve CI | Source/schematic/PCB/BOM/CPL and required evidence agree; production/bench claims remain separate |

Prefer existing `scripts/schgen/`, `scripts/pcb/`, component owners and check entrypoints. There is no assumption that OSC routing matrices or its native wrapper exist here. Inspect `.github/workflows/pr-checks.yml`, `component-spec-skills.yml` and `main-deploy.yml`; they are not a generic compute dispatcher. An additional compute workflow is a separately reviewed implementation.

Baseline/check surface: `pnpm circuit:check`, relevant strict component/integration and schematic tests, `pnpm check`, `pnpm build`, `pnpm check:site`, and the appropriate native/CAD/variant verifier. `pnpm b4push` already has one outer heavy guard; do not nest guards around its subcommands. Browser smoke follows the existing two-guard contract. Resolve current package/tool pins rather than copying versions from OSC.

## Campaign control

At kickoff write the real campaign/manager/dispatcher, task-to-issue/branch/session map, numeric shared-account allocation and CI reserve, measured VM budgets, model choices, finite attempt/deadline limits and authorized artifacts under `campaigns/<campaign-id>/`. All those values are currently unassigned, not unlimited. Preserve local-only originals and stopped evidence. If all remaining tasks need owner/bench evidence, report that boundary rather than rerouting unchanged boards.

The current DNS-incident deferral in ORCHESTRATION applies only to the matching observed signature; it is not proof of a failure here. Ordinary `main-deploy.yml` may build/publish the documentation after an authorized main update when its existing credentials/domain gates allow it. Do not alter those gates or run separate deployment commands.

## Historical 2026-11-12 rollout validation boundary

This rollout changes operating Markdown and agent entry links only. No circuit, firmware, native pin, workflow, evidence receipt, release package or generated output changes. Original entry-file bytes were hash-checked before adding links; new text, links and scope were reviewed. Full `pnpm`/native/build checks were NOT RUN in the rollout host (no pnpm, Node 22 rather than project Node 24, and direct GitHub DNS failure prevented a runnable checkout). This is not a passing engineering test or a standing waiver.
