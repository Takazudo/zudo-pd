# Circuit workflow

This is the canonical working agreement between this project and its AI agents. `CLAUDE.md` and `AGENTS.md` only point here. Every agent, whatever tool it runs in, follows this file.

The goal is that a short request such as "download this datasheet", "get the 3D model" or "check this spec" becomes durable, honest project knowledge: exact identity, retained evidence, regenerated documentation and a truthful statement of what is still unknown.

Routine work that the request already covers (downloads, evidence updates, regeneration, checks) needs no extra permission prompt. Ask one focused question only when a missing exact identity, design choice or external access prevents a meaningful result.

## Shared entry

Do this at the start of every task.

1. Read the project brief [`project/index.mdx`](../doc/src/content/docs/project/index.mdx) and [`project/next-actions.mdx`](../doc/src/content/docs/project/next-actions.mdx).
2. Read the inventory (`.claude/skills/component-spec-audit/references/inventory.json`) and the owner bundles and integration rules relevant to the request.
3. Run `pnpm circuit:check` **before** editing anything. Note what already fails, so pre-existing gaps are not confused with the ones your edit introduces.
4. Route by **exact manufacturer + complete MPN (including package/suffix) + supplier order code + project role**. A bare base name, family name or package name is not enough to resolve an identity, even when only one match seems plausible. When more than one record could match, report the ambiguity.
5. For a multi-step task, keep a short work note: the requested result, affected records and files, existing uncertainty, actions taken, new evidence and remaining work. A trivial download whose source record already carries the receipt does not need a separate note.

## Layout and ownership

| Path | What it is | Owner | Edit by hand? |
| --- | --- | --- | --- |
| `doc/src/content/docs/{project,architecture,research,decisions,verification}/` | Authored narrative: intent, rationale, decisions, plans, handoff | Project | Yes |
| `circuit/WORKFLOW.md`, `circuit/agent-task-examples.md`, `circuit/templates/` | This agreement, request examples, unpublished authoring templates | Project | Yes |
| `.claude/skills/component-*/` | Owner evidence bundles (v1 contract), one per exact component or group | Project | Yes, following the contract |
| `.claude/skills/component-spec-audit/references/inventory.json` | Orderable identities and declared placements | Project | Yes |
| `.claude/skills/component-spec-audit/references/direct-routing.json`, `external-vendor-qualifiers.json` | Routing cases and vendor qualifiers | Project | Yes |
| `.claude/skills/circuit-spec-integration/references/rules.json` | Cross-component integration rules | Project | Yes |
| `circuit/publication/selection.json` | What is published: record, source and linkable-source IDs, document selections, `expect` count locks | Project | Yes, as a reviewed diff |
| `circuit/publication/assets.json` | Allowlist of files deliberately published under `doc/public/` | Project | Yes, as a reviewed diff |
| `circuit/cad-receipts/` | CAD asset receipts (see Workflow D), created when the first asset is acquired | Project | Yes |
| `.circuit-cache/sources/` | Local working copies of downloaded sources (git-ignored) | Project, local only | Yes |
| `circuit.config.ts` | Project configuration read by the CLI | Project | Yes |
| `doc/zfb.config.ts` | Site config: header nav, sidebar categories, features | Project | Yes |
| `doc/src/**` outside `content/docs/` | Chrome bindings, styles and other site-shell code | Project | Yes |
| `doc/public/**` except `doc/public/assets/component-previews/` | Files you publish by hand (favicons, downloadable drawings, …) | Project | Yes, listed in `circuit/publication/assets.json` when restricted |
| Root `package.json` `scripts` | The project's command surface (`pnpm check`, `pnpm build`, …) | Project | Yes |
| `doc/src/content/docs/components/**` | Generated catalog, record and integration pages | Generator | **Never** |
| `circuit/generated/preflight.json` | Generated preflight report | Generator | **Never** |
| `doc/public/assets/component-previews/**` | Generated footprint SVGs and published WRL models | Generator | **Never** |
| `node_modules/@takazudo/zudo-circuit-doc/` | Renderer, validator, contract and component template | Package | **Never** |

Generated MDX is never hand-edited. Change the evidence or the selection, then regenerate. A hand-edited generated file is reported as drift by `pnpm check`; one with its generated marker removed is reported as an ownership conflict.

The five authored sections above (`project`, `architecture`, `research`, `decisions`, `verification`) are a default, not a ceiling — see [Adding an authored section](#adding-an-authored-section) to add your own.

## Adding an authored section

A project may add its own top-level authored section (for example `testing/` or `manufacturing/`) alongside the five defaults.

1. Add the content under `doc/src/content/docs/<section>/`, with an `index.mdx` as the section's landing page.
2. Give it a matching `categoryMatch` (equal to the section's directory name) wherever it appears in `headerNav` in `doc/zfb.config.ts`. Without a matching `categoryMatch`, the section's sidebar stays empty even though the pages exist.
3. The header nav is capped at **6 top-level items** (zudo-doc 5.27.0; the zudo-circuit-doc project documentation's "Getting started → What you get" page states the same cap). Project, Architecture, Research, Decisions, Verification and Components already fill it, so add the new section as a `children` entry under one of the existing dropdown items instead of a seventh top-level entry.
4. `project/index.mdx` and `project/next-actions.mdx` stay required regardless of what you add — the Shared entry above reads them first, on every task.

## Commands

Run these from the project root.

| Command | Does | Network |
| --- | --- | --- |
| `pnpm circuit:check` | Canonical offline validation of the evidence contract (`zudo-circuit-doc validate`) | No |
| `pnpm circuit:generate` | Regenerate component pages and the preflight report (`zudo-circuit-doc generate`) | No |
| `pnpm circuit:doctor` | Report required and optional tools (`zudo-circuit-doc doctor`) | No |
| `pnpm check` | Validate, compare a dry-run generation against committed output, check previews, type-check the doc site | No |
| `pnpm build` | Publish selected models, generate, build the site | No |
| `pnpm check:site` | Post-build checks: built references, publication scan, strict link check | No |
| `pnpm dev` | Dev server with generation in watch mode | No |
| `pnpm previews:generate` | Render footprint SVG previews with the pinned KiCad Docker image (`zudo-circuit-doc footprints generate`) | Image pull only |
| `pnpm exec zudo-circuit-doc new-component <suffix>` | Create an owner bundle `.claude/skills/component-<suffix>/` from the package template | No |
| `pnpm exec zudo-circuit-doc validate --online` | Re-download every non-volatile source and compare hashes; never alters retained evidence | **Yes** |
| `pnpm exec zudo-circuit-doc validate --refresh-source <SOURCE_ID>` | Re-download named sources only | **Yes** |
| `pnpm exec zudo-circuit-doc validate --json` | Same validation, machine-readable | No |
| `pnpm exec zudo-circuit-doc models` / `models --check` | Publish or check the selected WRL models | No |
| `pnpm exec zudo-circuit-doc footprints check` | Check committed footprint previews against their inputs | No |
| `pnpm exec zudo-circuit-doc check-browser` | Browser smoke of the built site with system Chrome, using `browserSmoke.representatives` or, absent that, up to 3 derived representatives | No |

Exit codes: `0` pass, `1` check failed, `2` usage or config error, `4` not run because an optional tool (Docker, Chrome) is missing. Exit `4` is "not run", never "passed". What each check does and does not prove is in [checks/README.md](./checks/README.md).

The documentation build never goes online. `--online` and `--refresh-source` are explicit agent operations for acquisition and refresh only.

## Evidence contract essentials

The frozen contract prose is [`.claude/skills/component-spec-audit/references/contract.md`](../.claude/skills/component-spec-audit/references/contract.md); the package's own copy, [contract.md](../node_modules/@takazudo/zudo-circuit-doc/contract/contract.md) (available after `pnpm install`), is the fallback if the skill copy is ever missing. The summary below does not replace either.

### Files of a v1 owner bundle

| File | Role |
| --- | --- |
| `manifest.json` | Exact record identity, parentage, and the assigned source, fact and interaction IDs |
| `sources.json` | Source authority, availability, document revision, URL, hash, locator and retained extract |
| `facts.json` | Typed claims: value, unit, conditions, provenance, verdict and calculation dependencies |
| `coverage.json` | Declared domain coverage with explicit reasons and `blocking_fact_ids` |
| `routing.json` | Positive and negative routing cases to the exact owner |
| `interactions.json` | Component-level interaction knowledge |
| `pin-map.json` | Source-backed pin identity and project mapping (symbol pin, footprint pad, net) |
| `SKILL.md` | Owner-bundle entry instructions |

The inventory holds orderable identities and placements; the owner bundle holds evidence. Standalone and subordinate records follow the same rules: parentage changes organization, never rigor. A subordinate gets its own record, source, fact, interaction, routing, coverage and pin-map IDs.

### Verdicts

Only these six verdicts are valid, spelled exactly:

| Verdict | Meaning |
| --- | --- |
| `PASS - primary-source confirmed` | A qualifying primary claim, or a calculation whose whole dependency closure is primary PASS |
| `CONFIRMED - distributor identity only` | Narrow order-identity confirmation; never performance evidence |
| `BLOCKER - deterministic spec violation` | A supported, deterministic violation |
| `NEEDS BENCH` | Requires measurement or physical verification |
| `UNSOURCED` | Required support is not retained |
| `NOT APPLICABLE` | The claim or domain does not apply, with a reason; it never blocks a domain |

Do not collapse these into a single pass/fail field anywhere, including in reports.

### Provenance, authority and availability

- Provenance values: `PRIMARY-SPEC`, `DISTRIBUTOR-IDENTITY`, `REFERENCE-DESIGN`, `CALCULATED`, `PROJECT-CHOICE`, `BENCH-OBSERVED`, `UNVERIFIED`. Provenance and verdict are separate fields.
- `PRIMARY-SPEC` may be PASS only from an `AVAILABLE` `MANUFACTURER_PRIMARY` source. `CONFIRMED - distributor identity only` needs an `AVAILABLE` `DISTRIBUTOR_IDENTITY` source and a `PROJECT_STATE` identity fact.
- **Availability is not authority.** A downloaded distributor page is available but not primary. A correct manufacturer URL is authoritative in origin but may be unavailable.
- An unavailable source has availability `SOURCE UNAVAILABLE` and the **zero-hash sentinel**: a SHA-256 of 64 zeros. It records the absence of verified bytes, not a digest. Never write a guessed or copied hash.
- A hash belongs to the bytes actually inspected. A URL can later serve different bytes; an old hash is not proof of current remote content.

### Locators

A source lock records both `physical_pdf_page_index` and `printed_page_label`. The physical index is **0-based**: the first page of the PDF file is `0`, whatever is printed on it. The printed label is the page number as printed on the page (which may be roman, prefixed, or absent). They often differ; record both. Add an exact section, table, figure or row locator and a minimal normalized extract, enough to audit the claim without redistributing the document.

### Conditions and scope

Keep absolute maximum distinct from recommended operation, typical curves distinct from guaranteed limits, clamp distinct from standoff and breakdown, and project state distinct from manufacturer behavior. Every quantitative fact carries an explicit unit and its conditions; textual facts use unit `NONE`.

### Calculations

A `CALCULATED` fact lists its raw fact IDs in `depends_on` and an evaluable arithmetic `expression` that names exactly those IDs. Missing, unused, self and cyclic dependencies fail. A calculated PASS is trusted only when every raw leaf of its **dependency closure** is a primary-source PASS; a figure computed from a typical value stays dependent on typical evidence.

The validator recomputes the arithmetic. **Arithmetic is not dimensional proof:** it does not check units algebraically or prove the source table was read correctly. Unit consistency and table interpretation remain an explicit review step for the agent.

### Coverage

`COVERED` means the declared domain has available, non-`UNSOURCED` evidence for its listed facts. **`COVERED` is not hardware sign-off**: a `NEEDS BENCH` fact can still count as available evidence. Report explicit verdicts, never a summary "safe" badge. Every `OPEN` domain names its blocking facts in `blocking_fact_ids`.

## Workflow A — start a circuit

**Input:** an idea, constraints, sketches or an existing design.

1. Fill the brief in `doc/src/content/docs/project/index.mdx`: intended behavior, interfaces, power source, dimensions, environment, quantity, constraints and unknowns. Keep "Not entered" where the owner has not said.
2. Draft functional blocks and operating states in `doc/src/content/docs/architecture/overview.mdx`. Name the decisions that constrain component selection. Start from responsibilities, not IC names.
3. Record candidate components as authored research (copy `circuit/templates/project-docs/research/component-candidate.mdx` into `doc/src/content/docs/research/`). Candidates stay out of the inventory until selected.
4. Put the most consequential uncertainties and the next bounded task in `doc/src/content/docs/project/next-actions.mdx`.
5. Add integration rules only when a real interaction exists (see [Integration rules](#integration-rules)).
6. Run `pnpm circuit:check` and `pnpm check`.

**Done:** another agent can explain the goal and the next decision from the brief, the overview and next actions alone, without the original conversation. Unknown electrical values remain unknown; none was invented to fill a table.

## Workflow B — add or replace an exact component

**Input:** an exact part or link, its function, a proposed placement, or a requested substitution. The step-by-step checklist is [new-component-workflow.md](../.claude/skills/component-spec-audit/references/new-component-workflow.md).

1. **Resolve identity:** manufacturer, complete MPN with suffix and package variant, supplier order codes, and population intent (fitted, not fitted, hand-fitted, external).
2. **Find or create the owner.** Reuse an existing owner bundle, or create one:

   ```sh
   pnpm exec zudo-circuit-doc new-component <suffix>
   ```

   This copies the package template to `.claude/skills/component-<suffix>/`. It contains deliberate placeholder values; replace **every** one. The validator fails on any placeholder left behind.
3. **Obtain evidence** through Workflow C. Record identity, ratings, pinout, defaults, conditions and relevant behavior at the granularity the design needs.
4. **Map pins:** symbol pins, footprint pads and current nets in `pin-map.json`. Board placement is project state with its own revision.
5. **Update the inventory** (`.claude/skills/component-spec-audit/references/inventory.json`, manual profile):
   - One line per orderable identity. Identity is a unique `line_id` plus a unique (manufacturer, complete MPN) pair. The line's `mpn`, `manufacturer`, `lcsc` and `package` must equal the owner record's.
   - `lcsc` is required but may be `""`. A non-empty value must be a real LCSC C-number read from the supplier listing for this exact part. **Never fabricate or guess a C-number**; leave it empty when the part is not on LCSC or not yet checked.
   - `suppliers: [{ "supplier": …, "order_code": … }]` is optional and display-only; it does not create routing aliases.
   - `placements` lists board and reference designator. It may be `[]`. Placements are **declared, not verified**: the manual profile does not bind them to a schematic.
   - Update the reviewed `assertions` counts. Add the line's direct-routing cases to `direct-routing.json` (one set per line is mandatory once the file is configured).
6. **Read the `SCOPE:` line** printed by `pnpm circuit:check`. It states that the manual inventory provider performed no schematic or placement binding, how many lines and declared placements it saw, and whether the pin-asset check ran or was skipped because CAD is disabled. That line is the honest limit of what the check proved; repeat it in the report.
7. **Obtain CAD** through Workflow D if the part goes on a board.
8. **Update the publication selection in the same task** (see [Publication policy](#publication-policy)), then `pnpm circuit:generate`, `pnpm check`, and `pnpm build` followed by `pnpm check:site`.
9. **For a substitution,** compare electrical, firmware, startup, thermal and mechanical dependencies of both exact parts, and record changed design decisions explicitly (use a change-impact note).

**Done:** one exact identity is traceable from the inventory through its owner bundle, pin map and published page; every outstanding gap is visible as an `OPEN` domain or a non-PASS verdict; the selection diff is part of the change. "Added to the catalog" does not mean "suitable for production".

## Workflow C — find or download a datasheet or source

**Input:** an exact component and the fact(s) that need evidence.

1. Reuse a retained source if its identity, revision and scope meet the task.
2. Prefer manufacturer-primary documents for performance claims. A distributor page may establish order identity only, in the narrow identity lane.
3. Fetch the actual bytes into the local cache, following redirects and keeping the response headers:

   ```sh
   mkdir -p .circuit-cache/sources/<SOURCE_ID>
   curl -fsSL --max-redirs 10 -D .circuit-cache/sources/<SOURCE_ID>/headers.txt \
     -o .circuit-cache/sources/<SOURCE_ID>/document.pdf "<URL>"
   head -c 5 .circuit-cache/sources/<SOURCE_ID>/document.pdf   # must print %PDF-
   sha256sum .circuit-cache/sources/<SOURCE_ID>/document.pdf
   ```

4. **Reject HTML posing as a PDF.** A file whose first bytes are not `%PDF-`, whose `Content-Type` header is `text/html`, or which contains `<html` or a login, captcha or error page is **not** a datasheet, whatever its URL or filename says. Then open the PDF and confirm the title, document number and part list cover the exact MPN and package before relying on it.
5. Record in `sources.json`: title, document number, revision and date, authoritative URL, retrieval date, authority class, availability, SHA-256 of the inspected bytes, `physical_pdf_page_index` (0-based), `printed_page_label`, the exact locator and a minimal extract.
6. Inspect pin diagrams, tables and graphs visually when text extraction loses their meaning.
7. Refresh the affected facts and their dependency closure. A download that succeeds does not make every fact PASS; each claim is checked against its own locator.
8. Regenerate (`pnpm circuit:generate`) and run `pnpm circuit:check`.

### Retention policy

| Storage | Location | Committed | Meaning |
| --- | --- | --- | --- |
| Working cache | `.circuit-cache/sources/<SOURCE_ID>/` | No (git-ignored) | Convenient local bytes; reproducible only while the URL still serves the same bytes (compare the recorded hash) |
| Project-retained archive | A committed directory the project chooses, for example `circuit/source-archive/` | Yes | Durable bytes, only when the project decides to keep them and the source's terms allow it |
| Public selected asset | `doc/public/...`, listed in `circuit/publication/assets.json` | Yes | A deliberate documentation download; requires permission to redistribute |

The evidence record, not the cached file, is authoritative. Nothing under `.circuit-cache/` is published or relied on by the build.

### SOURCE UNAVAILABLE procedure

If acquisition is blocked (paywall, login, bot wall, dead link, transport error):

1. Keep the source entry with availability `SOURCE UNAVAILABLE` and the zero-hash sentinel. Record the attempted URL, the date and the genuine reason in the locator or extract.
2. Give facts that depend on it the verdict `UNSOURCED` (or keep them unresolved); list them in the relevant `OPEN` coverage entry's `blocking_fact_ids`.
3. Do not borrow values from a same-name part, a family datasheet or memory, and do not create an empty file and call it a download.
4. Add the retry to next actions. When the source becomes available later, inspect it and update claims one by one; never bulk-promote facts.

**Done:** the next agent can find exactly which bytes were consulted (or why none were), and which facts each source supports.

## Workflow D — obtain symbol, footprint and 3D model

**Input:** the exact orderable variant and its intended board or mechanical use. CAD checks run only when `cad.enabled` is `true` in `circuit.config.ts`, with its symbol libraries, footprint roots and model root configured; otherwise the pin-asset check is reported as SKIPPED.

A complete enabled block, with real values taken from this repository's own `examples/minimal/circuit.config.ts`:

```ts
import type { CircuitConfig } from "@takazudo/zudo-circuit-doc/config";
import { DEFAULT_PREVIEW_RENDERER } from "@takazudo/zudo-circuit-doc/config";

export default {
  // ...
  cad: {
    enabled: true,
    libraryName: "example-minimal-circuit-lib",
    symbolLibraries: ["symbols/example-minimal-circuit-lib.kicad_sym"],
    footprintMasterRoot: "footprints/kicad",
    footprintLibraryRoot: "footprints/kicad/example-minimal-circuit-lib.pretty",
    modelRoot: "footprints/kicad/example-minimal-circuit-lib.3dshapes",
    modelLocatorPrefix: "${KIPRJMOD}/../../footprints/kicad/example-minimal-circuit-lib.3dshapes/",
    previewRenderer: DEFAULT_PREVIEW_RENDERER,
  },
  // ...
} satisfies CircuitConfig;
```

- `libraryName` — the KiCad library name the project's symbols and footprints live under.
- `symbolLibraries` — one or more `.kicad_sym` paths merged for pin lookups.
- `footprintMasterRoot` / `footprintLibraryRoot` — the canonical footprint directory and the `.pretty` library directory the check keeps byte-identical (`cmp -s`) when both are configured.
- `modelRoot` — the `.3dshapes` directory holding the published WRL models (and any optional STEP siblings).
- `modelLocatorPrefix` — the `${KIPRJMOD}`-relative prefix written into a footprint's 3D-model reference.
- `previewRenderer` — reuse the package's `DEFAULT_PREVIEW_RENDERER` (`import { DEFAULT_PREVIEW_RENDERER } from "@takazudo/zudo-circuit-doc/config"`; the pinned KiCad Docker image, version, platform, render layers and theme) unless the project needs a different renderer. A missing rendered preview means running `pnpm previews:generate`, not hand-authoring one.

1. Resolve the exact part and package, and check whether the project already has the symbol, footprint or model.
2. Acquire assets, recording provider, exact product page, original filename, date and SHA-256 in a receipt. Keep the unmodified import next to any documented derived version.
   - **KiCad official libraries:** pin the library release tag you took files from and record it. The KiCad 9 official 3D library ships STEP only; a matching WRL may exist only in a tagged 8.x release. Use a pair from one tagged release or record the WRL as unavailable. The web viewer renders WRL only, and no STEP-to-WRL conversion is part of this workflow.
   - **LCSC-listed parts (optional):** `easyeda2kicad --lcsc_id <C-number> --footprint --symbol --3d --output .circuit-cache/cad/<part>` imports EasyEDA assets. Treat the result as an import to inspect, not as verified geometry.
3. Merge only the part's symbol into the configured symbol library; never overwrite a shared multi-symbol library file. If the config names both a footprint master root and a library root, keep the `.kicad_mod` byte-identical in both (`cmp -s`).
4. Check symbol pins and footprint pads against the exact datasheet: numbering, exposed pad, pin 1, polarity, pitch, drill, body envelope, mounting. `pnpm circuit:check` enforces that symbol pins, footprint pads and the pin map agree; it cannot tell whether they match the datasheet.
5. Check the 3D model's variant, units, axis and origin, scale, rotation, offset, seating plane and dimensions against the mechanical drawing.
6. Classify **fidelity** with the evidence for the label:

   | Fidelity | Meaning |
   | --- | --- |
   | `exact-vendor` | Published by the manufacturer for this exact orderable variant |
   | `family` | Represents the package or series, not proven for this variant (for example a generic library package) |
   | `derived` | Produced from an original by a recorded transformation; keep input hashes, script, parameters and output hashes |
   | `unavailable` | No usable asset; the state is documented, nothing is fabricated |

   A familiar shape is not proof of the exact variant.
7. Write the receipt from [templates/cad-asset-receipt.json](./templates/cad-asset-receipt.json) (and optionally the Markdown form) to `circuit/cad-receipts/<ASSET_ID>.receipt.json`.
8. Select the package for preview in `circuit/publication/selection.json` and update `expect.packages`, then regenerate: `pnpm previews:generate` (Docker), `pnpm exec zudo-circuit-doc footprints check`, `pnpm exec zudo-circuit-doc models`, `pnpm exec zudo-circuit-doc models --check`. Restart the dev server after adding an asset; it does not pick up new public files while running.
9. Report which checks were performed and which remain visual or physical.

A preview is a rendering result. **A preview is not dimensional proof**, and a footprint that imports cleanly does not prove pin correspondence or physical seating.

**Done:** a future agent can tell which file to use, why it matches, which fidelity class it has and on what evidence, and what the model cannot establish.

## Workflow E — verify a specification

**Input:** a claim, a component record, a design decision or a changed source.

1. Identify the exact claim, raw facts, units, conditions, provenance and source revision.
2. Classify the fact: absolute maximum, recommended operation, guaranteed characteristic, typical curve, transient or protection condition, thermal/SOA, or project state.
3. Inspect the primary evidence at its locator and compare the source condition with the intended use condition.
4. Recompute calculations with explicit `depends_on` and units. A calculation cannot gain stronger evidence than its raw inputs, and the arithmetic check does not prove dimensional correctness.
5. Where the conclusion depends on rails, startup and defaults, pins, harnesses, thermal assumptions or firmware, check the cross-component state too (integration rules).
6. Record one of the six verdicts with its reason. Keep `NEEDS BENCH` and `UNSOURCED` where they apply.
7. Regenerate, update the affected decision or open question, and run `pnpm circuit:check` and `pnpm check`.

**Done:** the claim's meaning, conditions and support are clear, with its locator, and the report says whether it is source-confirmed, violated, unsupported or awaiting measurement. A schema pass is not an electrical correctness result.

## Workflow F — record a bench result

**Input:** actual measurements or a user-supplied test log.

1. Use a verification report (copy `circuit/templates/project-docs/verification/bring-up.mdx` into `doc/src/content/docs/verification/`). Record board revision, population changes, firmware and configuration, instruments and setup, supply and load, ambient conditions, method, raw observations, the expected criterion with its basis, and the outcome.
2. Keep raw data and photographs linked. Preserve separate runs and rework states; a later success never overwrites an earlier failure.
3. Where a measurement becomes evidence, record it with provenance `BENCH-OBSERVED` from a `BENCH_RECORD` source. Never force a measurement into a manufacturer-primary PASS.
4. Scope the conclusion to the tested unit, configuration and conditions. On a failure, link the affected decision and add the next action.

**Done:** the observation, its conditions and its scope are recorded against one revision, only observed values are entered, and the affected coverage and next actions are updated.

## Workflow G — handle a source or design change

**Input:** an updated datasheet, a substitution, a footprint edit, a firmware change or a schematic/net change.

1. Find every reference to the affected source, fact and record IDs (search the owner bundles, `rules.json`, the selection and authored pages).
2. Evaluate stale project-state hashes, calculated dependencies, integration rules, pin maps, footprint and model hashes and authored decisions.
3. Update each affected item, or mark it pending with a reason. Do not clear unrelated unresolved items to get a clean output.
4. Never re-pin a source hash without inspecting the changed bytes.
5. Use a change-impact note (`circuit/templates/project-docs/project/change-impact.mdx`) when the change has downstream effects.
6. Regenerate and run `pnpm circuit:check`, `pnpm check` and, when publishable output changed, `pnpm build` and `pnpm check:site`.

**Done:** one small reviewable diff contains the evidence change, the design state, the regenerated pages and any revised decision; everything still pending is named with its reason.

## Integration rules

`.claude/skills/circuit-spec-integration/references/rules.json` starts as `{ "schema_version": 1, "rules": [] }`. An empty rule list is valid.

- Add a rule **only when a real interaction exists** between exact components (a shared rail, a logic-level boundary, a startup dependency, a thermal coupling). Name its records, fact IDs, conditions, verdict and refusal text, and any conditioned calculation.
- An evidence chain lists stages from official source through conditioned requirement, netlist, symbol/footprint, PCB orientation, BOM and placement, as-built, programmed and bench. **Stages stay `OPEN` with empty `fact_ids` until real evidence exists.** A completed early stage never implies a later one; a generated netlist is never `CONFIRMED`.
- Follow [circuit-spec-integration](../.claude/skills/circuit-spec-integration/SKILL.md) when a question spans more than one component.

## Publication policy

Adding evidence does not publish it. `circuit/publication/selection.json` lists exactly which record IDs, source IDs and linkable source IDs are published, one document selection per record (`documentKind` is `datasheet`, `specification` or `drawing`, chosen after inspecting the content), and the `expect` counts (`records`, `sources`, `integrationRules`, `packages`) that lock the published set. Zero is allowed.

- Selection and assets-allowlist edits happen **in the same task** as the evidence change and show up as a reviewable diff. No per-part conversational permission prompt is needed; the diff is the review.
- Selecting a source publishes its metadata; an outbound link is published only for IDs in `linkableSourceIds`.
- Raw sources and CAD files stay outside `doc/public/`. A file placed there deliberately must be listed in `circuit/publication/assets.json` with a reason; the publication scan fails otherwise. Generated previews under `doc/public/assets/component-previews/` are the only exception.

## Tool matrix

| Tool | Status | Needed for |
| --- | --- | --- |
| Node.js ≥22.18 | Required | Everything |
| pnpm 11 (via corepack) | Required | Install and scripts |
| Python ≥3.10 (stdlib only) | Required | `pnpm circuit:check` (override the interpreter with `CIRCUIT_DOC_PYTHON`) |
| git | Required | History, review diffs, doc history |
| Docker + the pinned KiCad image | Optional | `pnpm previews:generate` |
| Chrome (or `CHROME_BIN`) | Optional | `zudo-circuit-doc check-browser` |
| Network | Optional | Acquisition and `--online` refresh only; never the build |
| easyeda2kicad | Optional | Importing assets for LCSC-listed parts |

`pnpm circuit:doctor` reports which of these are present. A missing optional tool gives exit `4` ("not run") for the command that needs it. The dev server must be restarted after adding an asset to `doc/public/` (zudo-doc behavior).

## Completion report

End every task with four parts:

1. **Obtained or checked:** what was downloaded, verified, generated or measured.
2. **Exact identity:** the manufacturer, complete MPN, package variant, source (document number, revision, locator) or asset (with its receipt and fidelity) involved.
3. **Changed:** the evidence records, authored pages, selection and generated outputs that changed, and the checks run with their actual results (including any `SCOPE:` and `SKIP:` lines).
4. **Remaining:** what is still open, each item with its reason (unavailable source, needs bench, needs a design decision).

Keep routine tool chatter out of the report. Update next actions when the project state has materially changed.

## zudo-pd authority and publication

Read the root `CLAUDE.md` and exact owner skills before component or hardware work.
`pnpm circuit:check` runs the strict project audit and forward-test gates before package validation.
The build repeats these gates before copying models or generating pages. Raw agent resources are withheld.
The generated catalog is a reviewed projection; it does not establish assembled or measured behavior.
Do not replace canonical owner skills with the initializer templates.
