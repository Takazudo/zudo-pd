# PD and LED repository and documentation consolidation

Accepted planning decision: **2026-11-16 JST (2026-11-15 UTC)**.
Tracking: [super epic #308](https://github.com/Takazudo/zudo-pd/issues/308). Execution: [Moya + Codex Cloud](moya-codex-cloud.md).
Status: **plan recorded; migration not started; no implementation sessions launched by this record**.

This plan is self-contained. The epic owns live progress, child links, decisions and
blockers; this file owns the accepted structure, migration sequence and acceptance
criteria. A later session must refresh the source snapshot before implementation.

## 1. Outcome and rationale

Consolidate `Takazudo/zudo-led-lamp` into `Takazudo/zudo-pd`, using
`Takazudo/zudo-circuit-doc` as the documentation framework. Keep one repository,
one documentation site and one canonical exact-component catalog. The framework
repository continues to own reusable tooling; it does not become the home for
PD/LED product documentation.

P15 is already the shared input board for LED and PD15. Separate repositories and
sites duplicate navigation, component evidence, status and source-reference work.
Readers should be able to choose a product and follow its design, current state,
manufacturing and verification without reconstructing the story across repositories.

The owner authorized the epic, README and planning-document updates in the current
session. Actual LED import, component consolidation, site migration and cutover are
work for the next user-started Moya + Codex Cloud implementation campaign. This plan
does not change circuit decisions, physical acceptance, version numbers or current
manufacturing packages. The next campaign records its own implementation and merge
authority; the current documentation update is not a standing grant for later work.

## 2. Inspected source snapshot

| Repository / work | Inspected revision | Role |
| --- | --- | --- |
| [zudo-pd](https://github.com/Takazudo/zudo-pd/tree/b377136d96f738a803a5dc5e8416402450dceeb7) | `b377136d96f738a803a5dc5e8416402450dceeb7` | Destination main, through PR #306 |
| [zudo-led-lamp](https://github.com/Takazudo/zudo-led-lamp/tree/88cb17409cf16a0391e8eadf0ad8a43d60a37356) | `88cb17409cf16a0391e8eadf0ad8a43d60a37356` | LED source and history to import |
| [zudo-circuit-doc](https://github.com/Takazudo/zudo-circuit-doc/tree/9e46d70ac7accfe98abce683d6f550274e6731d0) | `9e46d70ac7accfe98abce683d6f550274e6731d0` | Framework reference; runtime 0.4.0 at inspection |
| [zudo-osc-hole-field](https://github.com/Takazudo/zudo-osc-hole-field/tree/85b2b489d6f47b34991e3d9b0d2e09991a458a97) | `85b2b489d6f47b34991e3d9b0d2e09991a458a97` | Orchestration reference, not hardware or authority input |
| [PD20 PR #307](https://github.com/Takazudo/zudo-pd/pull/307) | `9312dc627df2de22d1ac44a3a05fbcb207665b3e` | Open, unmerged D2 layout work; separate from destination main |

At inspection PD had four open issues (#210, #228, #235, #279) and PR #307;
LED had eight open issues (#34, #35, #52, #68, #69, #143, #144, #145) and no open PRs.
These are dated observations, not permanent counts or instructions to close them.

## 3. Preserve hardware identities

| Stream | Canonical source / meaning | Boundary to preserve |
| --- | --- | --- |
| Shared P15 r1 | PD `boards/board-p15/`, `scripts/schgen/board_p15_spec.py`; STUSB4500, 15 V / 3 A | Same PCB, population and NVM for LED first, then PD15; one module owner |
| PD15 | `board-p15 + board-b` | +12 V / 1.2 A, -12 V / 0.8 A, +5 V / 0.5 A are targets; received S3 differs from later development substitutions |
| PD20 | `board-p + board-b20-draft` | Current 20 V Board P r3, 20 V / 5 A intent and 5 A e-marked cable; separate from P15 sharing; no degraded mode |
| LED Lamp | Shared P15 + existing Board L, firmware and enclosure | Old LED `boards/board-p/` is historical LED hardware, not PD's current 20 V Board P |

The P15 owner record is [shared-reference.json](../../boards/board-p15/shared-reference.json).
The LED consumer record is [p15-r1-reference.json](https://github.com/Takazudo/zudo-led-lamp/blob/88cb17409cf16a0391e8eadf0ad8a43d60a37356/boards/p15-r1-reference.json),
which pins PD commit `8af9e5569c2534c03ce132515d1ec11f4c3f83d3`.
The consumer directly pins the PCB and NVM image. The seven artifacts listed by
the upstream P15 owner record were byte-identical between the consumer's pinned
PD revision and the inspected PD main.
Recheck the actual blobs during C1; an old pin alone is not evidence of divergence.
Preserve the original provenance even when the consumer becomes local to this repository.

Use explicit labels such as **Shared P15 r1**, **20 V Board P r3**, **PD15 Board B**,
**PD20 B20** and **Legacy LED Board P**. Do not silently rename native files or infer
identity from the shared `board-p` basename.

## 4. Target repository and documentation ownership

Use `products/led-lamp/` as the initial LED import boundary, preserving its internal
relative layout. Keep the current PD native-board paths and shared P15 owner in place
for the first migration. C1 must prove the import strategy and path mapping; a later
cleanup can move additional sources only through a separate, reviewed mapping.

Import LED history so original commit identities remain reachable; do not rewrite
the history that evidence pins cite. An unsquashed history-preserving subtree merge
or equivalent verified import is suitable. Do not squash the import PR if that would
discard the original parent ancestry; verify the source commit objects and ancestry
from a fresh clone of the integrated destination. Preserve legacy source receipts and
as-ordered records. Path changes need new mapping records, not rewritten historical
hashes. `git log` availability alone does not prove the documentation history UI works.

Common component evidence, inventory and integration rules become a single maintained
corpus. Board-native CAD may retain product-specific namespaces where needed. Do not
overwrite same-named files or concatenate generated component pages. Leave only one
active owner of each shared fact; a preserved historical copy is clearly historical.

### Six documentation categories

| Category | Proposed route prefix | Canonical content |
| --- | --- | --- |
| Project | `/docs/project/` | Overall architecture, current status index, next actions, workflow and cross-product decisions |
| Shared P15 | `/docs/shared-p15/` | Shared circuit, six-pin interface, NVM, per-unit acceptance and fixed manufacturing handoff |
| PD15 | `/docs/pd15/` | P15 + Board B, received S3 identity, rail targets, assembly and complete-product tests |
| PD20 | `/docs/pd20/` | 20 V input + B20, OSC contract, D1-D12, 20 V NVM, manufacturing and T1-T8 |
| LED Lamp | `/docs/led-lamp/` | Board L, LED drive, firmware, enclosure, assembly and lamp qualification |
| Components | `/docs/components/` | One generated exact-component catalog, primary-source metadata, CAD and where-used references |

Within each product: **Overview -> Current state / Next actions -> Circuit / Interfaces
-> Manufacturing / Assembly -> Verification -> Decisions / History**.
The Project status index links the authoritative product records instead of becoming
a second detailed status ledger. P15 programming and acceptance are authored once;
LED and PD15 link to them. General STUSB4500 facts belong in Components, while 15 V
and 20 V NVM configurations and acceptance remain with their respective modules.

Use the existing `pd.takazudomodular.com` site as the initial unified destination.
Update the title and introduction to make LED visible. Keep the old LED site usable
until the new site is verified, then implement a per-page redirect/compatibility map.
Two independent sites are acceptable only as an explicitly temporary migration state.
Preserve old heading fragments and evidence anchors; a redirect to a home page is
not an adequate replacement for a cited technical page.

### Framework constraints to resolve in implementation

- `led-generator-v1` supports multiple specs and explicit board identities. Preserve
  fitted/DNP placement counts and candidate exclusions when normalizing the current
  PD placement-level and LED line-level inventory conventions.
- Generated component routes are fixed under `/docs/components/` in the inspected
  runtime, with globally unique record/source/fact IDs. Build one canonical catalog
  from reviewed evidence; do not run two independent catalogs into the same route.
- The inspected config has one evidence bundles root, inventory and integration-rules
  input. CAD supports multiple symbol libraries but a single configured footprint/model
  root set and library name. Two arbitrary evidence/CAD trees cannot simply be listed
  together. C3 must normalize identities or propose a narrowly scoped upstream change.
- Merge exact manufacturer + full MPN + package + order-code identities with their
  provenance. Equal names or LCSC IDs do not erase incompatible symbols, revisions,
  operating conditions or as-built records. Retain all unresolved facts and negative tests.
- Preserve PD's restricted publication policy. Review LED's raw-agent-resource exposure
  and every asset selection instead of automatically publishing the union of both sites.
  Vendor bytes remain in private `circuit-dev-resources`; large local-only assembly STEP
  files retain their storage and replay restrictions. Never use Git LFS.
- Current projects use circuit-doc 0.3.0, Doc 9.1.4 and ZFB 5.2.2; PD has local patches.
  The inspected 0.4.0 family requires Doc 10.0.3 and ZFB 6.0.1. An upgrade is a separate
  reviewed change with its own checks, not a prerequisite inferred from the phrase
  "use zudo-circuit-doc." Preserve [#210](https://github.com/Takazudo/zudo-pd/issues/210)
  bridges until upstream parity is demonstrated. Never run the initializer over the
  existing project as a replacement for migration.

Framework references at the inspected revision:
[inventory profiles](https://github.com/Takazudo/zudo-circuit-doc/blob/9e46d70ac7accfe98abce683d6f550274e6731d0/doc/src/content/docs/concepts/inventory-profiles.mdx),
[configuration](https://github.com/Takazudo/zudo-circuit-doc/blob/9e46d70ac7accfe98abce683d6f550274e6731d0/doc/src/content/docs/reference/config.mdx),
[ownership and upgrades](https://github.com/Takazudo/zudo-circuit-doc/blob/9e46d70ac7accfe98abce683d6f550274e6731d0/doc/src/content/docs/concepts/ownership-and-upgrades.mdx).

## 5. Implementation sequence and acceptance

The stable task keys below are planning keys, not invented issue numbers. Moya searches
for existing work and creates/reuses linked child issues at implementation kickoff.
Each child restates its scope, dependencies, allowed writes, checks and completion
criteria. Link both directions; use native sub-issue relationships only if supported.

| Key | Deliverable | Dependencies / completion criteria |
| --- | --- | --- |
| C0 | Record accepted plan and operating handoff | Epic, README, plan and runbook agree; planning-only changes reviewed and checked; actual publication state reported |
| C1 | Freeze migration baseline and ownership | Refresh heads, issues/PRs and running sessions; write import manifest, path/route/fragment/ID maps, immutable artifact list, child issue map and numeric execution allocation; disposition #307 overlap |
| C2 | Import LED source and history | C1; original commits and source bytes traceable, native relative paths resolve, legacy Board P distinguished, P15 remains one canonical source, old repo kept usable |
| C3 | Consolidate component evidence and shared P15 references | C2; unique IDs, exact part/CAD mapping, reviewed inventory/placement/DNP/candidate counts, no weakened evidence or repinned frozen receipts; generated catalog and shared-reference checks pass |
| C4 | Integrate workspace, scripts and CI | C2 and coordinated C3 paths; root-discovered workflows cover both products, package/tool choices explicit, LED host/ARM firmware and enclosure checks retained, P15 consumer check resolves local owner history |
| C5 | Build the unified documentation site | C3 + C4; six product/module categories, one Components catalog, current-vs-history reconciliation, old route/fragment map, search and model/enclosure views verified; runtime upgrade separately reviewed if selected |
| C6 | Cut over and reconcile backlog | C5; unified site verified, old LED routes mapped, repository notice and issue ownership reconciled within granted access, final manifest/accounting reviewed, rollback and remaining product work recorded |

C3 and C4 may overlap only with disjoint write ownership. Central evidence, inventory,
`circuit.config.ts`, package files, generated outputs and navigation have one writer
at a time. C1 may inventory and plan while #307 is open; broad moves that overlap its
changes wait for its disposition or an explicitly reconciled baseline. Do not use the
migration to merge, reject or redo #307's circuit work implicitly.

### C1 outputs: the first Codex Cloud task

Create a campaign directory under `circuit/orchestration/campaigns/<campaign-id>/`
with a `plan.md`, a machine-readable baseline manifest and mapping tables. Record:

1. Exact source commits, current PR heads, existing open issues and any live writers/jobs.
2. Every imported path, canonical owner, proposed destination and treatment of generated
   files; include native library-relative paths, script working directories and Git history.
3. Component/evidence ID collisions, CAD namespaces, site routes/fragments/assets,
   firmware/tool pins, CI triggers/concurrency/preview markers and publication selections.
4. Protected source and artifact hashes, fixed package locks, current hardware state
   and the distinction between missing replay inputs and genuinely changed evidence.
5. Child issue/branch/session ownership, permitted parallel work, checks, rollback and
   one fully specified C2 task brief. Report actual capabilities, not assumed sessions.

This first task does not import LED or switch the public site. Its independently
reviewed manifest is the input contract for subsequent implementation.

### C4 details that must survive directory moves

Nested `.github/workflows/` are not active repository workflows. Move/adapt the required
LED checks into root workflows with correct working directories and path filters.
Resolve workflow/concurrency/preview-comment collisions. Preserve firmware host and
ARM builds, incremental/image checks, enclosure generation, and all required PD checks.
Do not replace one product's coverage with the other product's green badge.

PD currently pins pnpm 11.5.2 and Node 24; LED pins pnpm 10.34.1. Choose and validate
the resulting workspace deliberately. Preserve applicable package patches and each
native/preview tool binding. The LED P15 checker relies on historical Git objects;
prove that its full owner-reference check works after import, rather than retaining
only `--local-only`. Verify history rendering and asset paths after moves.

## 6. Existing hardware program and next work

[#228](https://github.com/Takazudo/zudo-pd/issues/228) remains the existing hardware
completion tracker. The consolidation epic coordinates repository/site delivery and
links that program; it does not replace it or require all bench work before migration
can complete. Read source and newer decisions as current authority; older comments
retain their original date and may contain superseded holds.

| Stream | Inspected state / next action to retain |
| --- | --- |
| Shared P15 | Two assembled P15 units planned; not ordered/received/programmed/measured in inspected records. Preserve the fixed package, supplier preview/current quote steps and mandatory per-unit 5 V provisioning, readback, power cycle and 15 V contract acceptance before either load |
| LED Lamp | Reuse two existing Board L units; no new L/B order in the P15 plan. Preserve RS1 = 200 mOhm and firmware `CTRL_FULL_CCR = 2407`; firmware remains an unflashed bench candidate. Qualify accepted P15 with LED first, including physical enclosure/assembly tests |
| PD15 | Reconcile received S3 Board B identity, usable quantity, LED2/D1 inspection and later source substitutions; then qualify the P15 + B combination and printed supports |
| PD20 | #307 is the open D2 layout change. Review its actual head, model/route-resistance and fill evidence, then reconcile order-gate wording. Preserve 20 V NVM binary work and all T1-T8 physical obligations |

PD20's latest direction identifies D2 PCB work as the remaining implementation hold,
while detailed D10/D12 rows and other pages retain older wording. C5 must reconcile
these against the latest decisions without inventing order readiness. The D4 official
GUI evidence settles POWER_ONLY_ABOVE_5V at 0xE6 bit 3; it does not create a reviewed
program-ready binary or settle reset/downgrade bench behavior. Some T5 prose still
describes the superseded discharge resistors; retain historical receipts and update
the current procedure from the adopted final design.

Relevant existing work stays open until its own acceptance is met:
[#210](https://github.com/Takazudo/zudo-pd/issues/210) (framework compatibility bridges),
[#235](https://github.com/Takazudo/zudo-pd/issues/235) (PD20 pre-order evidence),
[#279](https://github.com/Takazudo/zudo-pd/issues/279) (B20 comparator/back-feed scope),
and the LED issues listed in the snapshot. Classify implemented, physical, historical,
candidate and framework work explicitly. Do not transfer or close issues by age or
because their files moved. Preserve original issue URLs and remaining requirements.

Authoritative hardware owners remain [current state](../../doc/src/content/docs/project/current-state.md),
[release readiness](../../doc/src/content/docs/architecture/release-readiness.md),
[prototype-order readiness](../../manufacturing/prototype-order-readiness.md) and
the product-specific verification pages until their reviewed migration is integrated.

## 7. Verification, cutover and completion

Record baseline checks before changes and the same applicable checks on the final
integration revision. Use the repository's current pins and commands, including
`pnpm circuit:check`, `pnpm check`, `pnpm build`, `pnpm check:site`, generated-output
determinism and the full `pnpm b4push` gate. Retain applicable LED firmware/enclosure
checks. Native verification is required when its source/path/tool bindings are affected;
an unchanged source hash may support reuse only within the original report's scope.

The cutover review must establish all of the following:

- Every source/history/evidence item in the manifest is accounted for, with no unexplained
  omission, overwrite, changed frozen lock or manufactured physical success.
- One P15 owner and one exact-component catalog serve both consumers, while PD20's
  input/NVM/qualification remain separate. Generated output is deterministic.
- Each of the six categories leads to a current state and next action. Browser review
  covers navigation, search, small/large layouts, component/model viewers and LED-specific
  visual content. The `categoryMatch` values match actual content directories.
- Old page/asset/fragment references resolve to the correct material. Historical page
  metadata is checked in the actual UI. Public asset selection has not expanded silently.
- Both products' required checks run from the unified root and the actual integration
  head passes required CI. Missing tools or browser evidence are `NOT RUN`, not PASS.
- Production and old-site redirect outcomes are verified separately from Git merge.
  A source/destination issue map and retained hardware backlog are linked from the site.
- The old LED repository is retained for history. Any read-only/archive action is a
  separately recorded cutover action after links and issue ownership work; never delete it.
- Recovery points identify the accepted PD/LED commits, previous site routing/configuration
  and how to revert a migration batch. Before cutover keep the old LED site operational;
  after a failed cutover preserve evidence, restore the last verified routing within
  authorized scope and record the exact state before another attempt.

Close a child only after its own acceptance and required integration are verified.
Close the consolidation epic when C0-C6 are delivered and residual product work has
durable owners, even if legitimate physical qualification remains under #228.
This is documentation/repository completion, not a manufacturing release.

## 8. Next-session entry

Give Moya the epic URL and [the execution handoff](moya-codex-cloud.md#kickoff-prompt).
The first result should be the reviewed C1 baseline and bounded C2 brief. There is no
need to repeat the design discussion or create another umbrella tracker.
