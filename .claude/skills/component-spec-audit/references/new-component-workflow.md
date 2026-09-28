# New BOM component workflow

Run these steps from the repository root, in order. This checklist owns a new or
replacement BOM part from circuit identity through the committed public reference.
It does not authorize an unresolved electrical or firmware design change.

## Preconditions

Resolve the exact MPN, LCSC ID, manufacturer, board/refdes, symbol, package, pin map,
connectivity, per-placement DNP state, source authority, and intended public document
names before editing. Do not invent a refdes, pin, fact, or document kind to make the
workflow progress; stop and obtain the missing design or review decision.

## 1. Lock the circuit identity

1. Add the exact MPN, LCSC ID, symbol, footprint, fields, pins, and connectivity to
   the matching spec among `scripts/schgen/board_a_spec.py`, `board_b_spec.py`, and
   `board_p_spec.py`, then regenerate the matching committed schematic with the schgen
   entry point for that board and commit the edited spec and generated `.kicad_sch`
   together. The footprint field is
   `zudo-pd:<package>`; the validator rejects any other library nickname.
2. Add or update the exact line in
   `.claude/skills/component-spec-audit/references/inventory.json`, with one
   `placements[]` entry per board/refdes carrying its own reviewed `dnp` flag. The
   `led-generator-v1` provider binds placements against the Board A, Board B and Board P
   generator specs. Update the reviewed `assertions` and generator expectations through
   their normal reviewed workflow; do not change validator constants to accommodate
   corpus growth, and never put `dnp` on the line.
3. For a replacement part that no board places yet, add it to
   `references/candidates.json` instead. It carries the same identity fields plus the
   line it would replace, and it never reuses a placed LCSC.

## 2. Build the evidence owner

1. Copy `assets/component-skill-template/` to
   `.claude/skills/component-<exact-part>/` and replace every example value.
   If this creates or changes an owner assignment, update the exact-owner map in root
   `CLAUDE.md`; root routing stays a map to this owner workflow, not a second workflow.
2. Fill `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
   `routing.json`, `interactions.json`, and `pin-map.json` from audited sources.
   Record fact conditions, coverage, routes, interactions, and the real pin map;
   retain short normalized extracts, not PDFs. Each record sets exactly one of
   `line_id` and `candidate_id`.
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
   `.claude/skills/circuit-spec-integration/references/rules.json`, their domains in
   `references/schema.json` `integration_domains`, and their forward tests when the part
   affects another component or domain. If those rules change, update
   `references/observed-runs.json` too: its prompt/response SHA-256 values lock
   explicit-skill policy rendering/refusal against the frozen evidence packet, while
   `forward-tests.json` separately proves deterministic routing and discovery parity.

## 3. Acquire KiCad and model assets

1. Acquire the symbol and canonical footprint. For an LCSC/EasyEDA import, use:

   ```sh
   easyeda2kicad --lcsc_id <LCSC_ID> --footprint --symbol --3d --output tmp/<part>
   ```

2. Merge only the imported symbol entry into `symbols/zudo-pd.kicad_sym`; never
   copy or overwrite the whole shared multi-symbol library. Put the canonical
   `.kicad_mod` in `footprints/kicad/` and an identical copy in
   `footprints/kicad/zudo-power.pretty/`, which is the library `fp-lib-table` binds to
   the `zudo-pd` nickname and the only one the validator reads; verify with
   `cmp -s footprints/kicad/<name>.kicad_mod footprints/kicad/zudo-power.pretty/<name>.kicad_mod`.
3. Symbol pin numbers and footprint pad numbers must agree exactly; the validator locks
   the pin map against both files and rejects a renumbering.

## 4. Choose what becomes public

1. Explicitly add the record and every public source to
   `circuit/publication/selection.json`,
   with exactly one audited document source plus its truthful document kind. Inspect the
   retrieved content: a product page or HTML denial is not a datasheet because its URL
   ends in `.pdf`. Retrieve the candidate only into ignored `tmp/pdfs/`, follow
   redirects, retain response headers, verify the first bytes are `%PDF-`, and inspect
   the document title/page content against the exact MPN before selecting it. This is
   dated human verification, not a build-time live URL check: re-audit on a changed
   URL/content or scheduled source refresh.
2. Select the footprint preview through the record pin map and canonical footprint; do
   not rely on discovery or a default selection.

## 5. Regenerate, review, and commit

1. Run the offline gates:

   ```sh
   PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/component-spec-audit/scripts/validate.py
   PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'
   PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/circuit-spec-integration/scripts/check_forward_tests.py
   ```

   Read every `STAGED-SKIP:` line before believing a PASS. This project already binds
   Board A, Board B and Board P and validates all 30 owner bundles; keep the validator
   in strict mode for each change.
2. From the repository root, run `pnpm circuit:generate`, review the exact corpus counts,
   then run `pnpm circuit:check`, `pnpm check`, `pnpm build`, and `pnpm check:site`.
   Commit reviewed generated output with its authored source changes; never hand-edit a
   generated file. Run `pnpm b4push` for the complete guarded local quality gate.
3. Opening the regenerated schematic in Eeschema, running ERC, and performing a visual
   pin/orientation review is still required. No offline gate substitutes for it.
