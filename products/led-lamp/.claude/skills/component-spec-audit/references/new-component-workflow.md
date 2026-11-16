# New BOM component workflow

Run these steps from the repository root, in order. This checklist owns a new or
replacement BOM part from circuit identity through the committed public reference.
It does not authorize an unresolved electrical or firmware design change.

## Preconditions

Resolve the exact MPN, LCSC ID, manufacturer, board/refdes, symbol, package, pin map,
connectivity, DNP state, source authority, and intended public document/preview names
before editing. Do not invent a refdes, pin, fact, model basename, or document kind to
make the workflow progress; stop and obtain the missing design or review decision.

## 1. Lock the circuit identity

1. Add the exact MPN, LCSC ID, symbol, footprint, fields, pins, and connectivity to
   `scripts/schgen/board_p_spec.py` or `scripts/schgen/board_l_spec.py`; regenerate
   the matching committed schematic with exactly one of:

   ```sh
   python3 scripts/schgen/gen_schematic.py board_p_spec
   python3 scripts/schgen/gen_schematic.py board_l_spec
   ```

   Run `scripts/schgen/verify.sh <project>` (for example `board-p`, `board-l`, or
   `swd-adapter`) when
   `kicad-cli` is available; commit the edited spec and generated `.kicad_sch`
   together.
2. Add or update the exact line in
   `.claude/skills/component-spec-audit/references/inventory.json`. Update its
   reviewed `assertions`; do not change validator constants to accommodate corpus
   growth.

## 2. Build the evidence owner

1. Copy `assets/component-skill-template/` to
   `.claude/skills/component-<exact-part>/` and replace every example value.
   If this creates or changes an owner assignment, update the exact-owner map in root
   `CLAUDE.md`; root routing stays a map to this owner workflow, not a second workflow.
2. Fill `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
   `routing.json`, `interactions.json`, and `pin-map.json` from audited sources.
   Record fact conditions, coverage, routes, interactions, and the real pin map;
   retain short normalized extracts, not PDFs.
3. Add the matching `## Human component reference` to the owner `SKILL.md`, linking
   every owned `/docs/components/records/<slug>/` page plus the catalog and
   integration pages. The JSON bundle remains authoritative.
4. Update the reviewed locks with the evidence: direct-routing negatives in
   `.claude/skills/component-spec-audit/fixtures/direct-routing.json`, real-pin locks
   in `fixtures/golden/real-pin-maps.json`, and any affected critical-fact fixture.
   Add a `fixtures/golden/critical-facts.json` entry only when the new fact is a
   validator-protected critical design claim; then update its paired review fixture.
   Do not add incidental facts merely to raise fixture coverage.
   Add cross-component rules in
   `.claude/skills/circuit-spec-integration/references/rules.json` and their forward
   tests when the part affects another component or domain. If those rules change,
   update `references/observed-runs.json` too: its prompt/response SHA-256 values lock
   explicit-skill policy rendering/refusal against the frozen evidence packet, while
   `forward-tests.json` separately proves deterministic routing and discovery parity.

## 3. Acquire KiCad and model assets

1. Acquire the symbol and canonical footprint. For an LCSC/EasyEDA import, use:

   ```sh
   easyeda2kicad --lcsc_id <LCSC_ID> --footprint --symbol --3d --output /tmp/<part>
   ```

2. Merge only the imported symbol entry into `symbols/zudo-led-lamp.kicad_sym`; never
   copy or overwrite the whole shared multi-symbol library. Put the canonical
   `.kicad_mod` in `footprints/kicad/` and an identical copy in
   `footprints/kicad/zudo-led-lamp.pretty/`; verify with
   `cmp -s footprints/kicad/<name>.kicad_mod footprints/kicad/zudo-led-lamp.pretty/<name>.kicad_mod`.
3. Put a matching same-basename `*.step` and `*.wrl` in
   `footprints/kicad/zudo-led-lamp.3dshapes/`. The canonical footprint must reference
   that WRL through `${KIPRJMOD}/../../footprints/kicad/zudo-led-lamp.3dshapes/` and
   carry reviewed offset, rotation, and scale transforms. Do not treat a STEP-only
   import as complete.

## 4. Choose what becomes public

1. Explicitly add the record to `recordIds`, every public source to `sourceIds`, and
   every approved outbound source URL to `linkableSourceIds` in
   `circuit/publication/selection.json` (schema: zudo-circuit-doc
   `reference/schemas`). Add exactly one audited
   document source plus its truthful `documentKind` (`datasheet`, `specification`, or
   `drawing`). Inspect the retrieved content: a product page or HTML denial is not a
   datasheet because its URL ends in `.pdf`.
   Retrieve the candidate only into ignored `tmp/pdfs/` (or another temporary path),
   follow redirects, retain response headers, verify the first bytes are `%PDF-`, and
   inspect the document title/page content against the exact MPN before selecting it.
   For example: `curl -fsSL --max-redirs 10 -D /tmp/<source>.headers -o
   tmp/pdfs/<source>.pdf <URL>` followed by `head -c 5 tmp/pdfs/<source>.pdf` and a
   PDF viewer/text extractor. This is dated human verification, not a build-time live
   URL check: re-audit on a changed URL/content or scheduled source refresh, then
   update `circuit/records/document-verification.json` (including `checkedOn`), a
   project-owned record the runtime does not read, and the selection.
2. Select the footprint and model preview through the record pin map and canonical
   footprint/model pair; do not rely on discovery or a default selection.

3. Update every deliberately reviewed count/shape lock that the changed selection
   reaches: the selection's `expect` block (records, sources, integration rules,
   packages), the `scan` floors and `browserSmoke` representatives in
   `circuit.config.ts`, and `circuit/policy.json` when a project gate changes. Keep
   these locks explicit and reviewed; do not weaken them into inferred counts.
   Leave dated historical verification narratives alone unless this change actually
   repeats and re-verifies that stated baseline.

## 5. Regenerate, review, and commit

1. Regenerate and check committed previews:

   ```sh
   pnpm --dir doc generate:footprint-previews
   pnpm --dir doc check:footprint-previews
   pnpm --dir doc generate:models
   pnpm --dir doc check:models
   ```

2. Regenerate component MDX and its committed preflight report, review the exact
   corpus counts, then run the focused pre-build checks:

   ```sh
   pnpm --dir doc generate:components
   PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/component-spec-audit/scripts/validate.py
   PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'
   PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/circuit-spec-integration/scripts/check_forward_tests.py
   pnpm --dir doc check
   pnpm --dir doc check:components
   ```

3. Run `pnpm b4push` from the repository root before delivery. It builds the current site before
   running the built-reference, artifact, and isolated doc-skill scans, so those gates
   never inspect missing or stale `doc/dist` output. Commit reviewed generated
   component MDX, `circuit/generated/preflight.json`, footprint previews, public WRL
   previews, and every changed generator-owned `doc/src/content/docs/claude*`
   projection with their authored source changes; never hand-edit generated files.
   Inspect them with:

   ```sh
   git add --intent-to-add -A -- doc/src/content/docs circuit/generated/preflight.json doc/public/assets/component-previews
   git diff --exit-code -- doc/src/content/docs circuit/generated/preflight.json doc/public/assets/component-previews
   ```

4. Check the new `/docs/components/records/<slug>/` route itself in the built output
   or on the PR preview. The PR smoke route is representative, not proof that a new
   route renders; this issue does not change CI smoke ownership. `verify.sh` reporting
   `SKIPPED` without `kicad-cli` also is not a substitute for opening the regenerated
   schematic in Eeschema, running ERC, and performing visual pin/orientation review.


## External panel components

A purchased, hand-wired panel component is not a PCB part. Declare it explicitly
in the board spec's `EXTERNAL_COMPONENTS` before `NETS`, with exact MPN,
manufacturer, package, supplier, order code and datasheet URL. Keep its LCSC and
PCB footprint fields empty, but set inventory `mounting: external` with matching
supplier/order code. The generator emits `in_bom yes` and `on_board no`.

Use an exact manufacturer terminal symbol and evidence owner. Its pin map sets
`mounting: external`, an empty `footprint`, and physical terminal numbers in
`footprint_pad`. Record this meaning explicitly; do not fabricate PCB pads or model geometry. The current public viewer publishes only PCB package models. A future external
model needs its own reviewed publication contract; do not attach it to a wire-pad
footprint or fabricate STEP geometry. The former WR11AS-only external model path
was removed when the lamp switched to JLCPCB C496154. Add separate
bare-copper wire pads to both footprint library locations, with an inventory
exclusion only for those real board features. Verify system assembly connectivity
and PCB exclusion separately. All PCB-component asset requirements remain intact.
