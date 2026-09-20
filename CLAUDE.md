# zudo-pd project guidance

## Repository storage

Never use Git LFS. Large assembled STEP previews are ignored local derivatives;
do not track them or upload them through another storage service without an
explicit user request. Keep source CAD, component models and printable STLs in
ordinary Git. See `manufacturing/local-only-assembly-previews.json` for the exact
omitted files and their original hashes. Frozen verification must still fail if
a required original local file is absent or changed; do not silently skip it.

## Current work and evidence boundary

This repository designs a USB-C PD supply for modular synthesizers. The renewal
separates a reusable **Board P** USB-PD input module from **Board B** synth conversion.
The previous generated **Board A** input design remains a reference. The root
combined-board KiCad project is the historical v0.4.0 assembly, not the renewed layout.

Start with `doc/src/content/docs/getting-started/` and `architecture/`. Earlier
`overview/`, `inbox/`, `learning/` and `misc/` pages are archived at stable URLs because
component records and bench history cite them. Do not use an archived assertion as
current design authority.

Output budgets are +12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A. They are design
targets, not measured ratings. The selected Board B chain now uses AP63201 at +13.44 V, LM2596 stages at
+6.519 V and −14.145 V, LT1963A positive regulators and LT3015-12 negative
regulation. Those selections replace the earlier L7812/L7805/CJ7912 headroom
defects. Full-load, low-line, thermal and transient qualification remains open;
PCB routing or a clean DRC cannot establish these measured properties.

Keep these output budgets while updating component evidence, integration
calculations, schematics and PCB together. The AP63201 stage is owned by
`.claude/skills/component-ap63201-power-stage/`; its ceramic-bank capacitance is a
curve-based project assumption, not a guaranteed manufacturer bound.

J10/J11 use DEALON DW254P-2X8-L0 / C4749189. Its shroud replaces custom printed guards.
Verify the conventional synth pin assignment against its exact pin map; pins 1–2
are −12 V. Do not carry the previous connector's orientation assumptions forward.

## Current screw-terminal revision

Board B is 110 × 85 mm with a plain left edge. Two top-side
WJ500V-5.08-2P / C8465 blocks replace the four Fastons, with wire entries facing
left. J6.1=GND, J6.2=−12 V, J7.1=+5 V and J7.2=+12 V. J8/J9 are retired.
Exact C8465 routing and evidence are owned by
`.claude/skills/component-kangnex-wj500v-5-08-2p-c8465/`.
The current board requires no printed terminal guard. Preserve earlier releases
and `3dp-files/faston-cover/` as historical artifacts; never apply its T-notch
contract or underside Faston positions to the active PCB.

Board B is installed on legs with its front/component face DOWN. J5 is on F.Cu.
Board P mates face-to-face on that side, front face down in CAD at nominal
Z=+11.1 mm; it is physically below B after installation. Board P's own PCB remains
unchanged. `pd_to_board_b` in `scripts/pcb/board_b_layout.py` maps `(x,y)` to `(y−0.5,x+12)`;
apply it to every P hole and mating pin. Do not restore the earlier bottom J5 or
in-plane `(y,27-x)` stack transform.

The three Ø3.2 mm PD holes are separate from four independent Ø3.0 mm HC-11
corner holes H4–H7, with each corner center 4 mm from adjacent edges. The exact
support evidence is `boards/board-b/supports/hc11-evidence.json` and its README.
The footprint's Ø6 mm Fab circle and 6.5 mm courtyard are project assumptions;
complete HC-11 head/base envelopes remain unknown. HC-11's 11 mm support height
conflicts with a flat floor below the front-down assembly: P substrate reaches
12.7 mm and the terminal drawing maximum reaches 14.2 mm. Do not present lateral
PD movement, nominal CAD clearance or a clean DRC as a resolution.

The selected accessory prototype is now the homemade printed adhesive leg in
[`3dp-files/adhesive-leg/README.md`](3dp-files/adhesive-leg/README.md). Its seating
height is 18 mm, with a 14 × 14 × 2 mm base and a straight Ø7 mm pole.
The exact 27-vertex untapped M3 aperture from the user's supplied reference
forms a 4.5 mm blind bore, with no taper or larger lower cavity. Use an M3 × 5 mm
screw as the initial fit candidate: through the 1.6 mm PCB it inserts 3.4 mm,
leaving 1.1 mm nominal clearance to the blind floor. The earlier M3 × 8 mm
recommendation is invalid for this bore; the previous design is archived under
`3dp-files/adhesive-leg/archive/tapered-pocket-v1/`.
Do not replace that profile with a fitted circular bore or add modeled threads.
The taller prototype addresses the nominal HC-11 height conflict, while printing,
adhesive strength, M3 passage and retention remain physically unmeasured. Existing
PCB corner holes remain 3.0 mm, with zero nominal diametral clearance for M3.
This accessory does not change the PCB or JLCPCB package. Keep its source and
verification separate from the frozen HC-11 evidence, board mechanical reports
and release files; those retain the earlier support assumption.

Retain front voltage labels and duplicate the four screw-terminal rail labels on
B.SilkS. Back text must read normally when viewed from the back, using mirrored
KiCad text. Verify both sides against the actual pin nets. P1 and TP3/TP4/TP5 retain
seven front-edge contacts: ATT, PDOK, GND, NC, +13.44 V PRE, +6.519 V PRE and
−14.145 V PRE. The row is shifted 20 mm right, with contact centers x=56.19–71.43 mm
at y=1.8 mm. P1.3 is their shared probe ground; preserve NC.

The current export destination is `manufacturing/releases/corner-support-review/`.
Earlier front-stack/terminal/guarded/compact/renewal review packages describe older revisions.
Ground-layout reports distinguish aggregate sampled copper width
from the largest individual run; neither proves one continuous corridor or rated
current. Require polygon-connectivity and specified ground-stitch checks as well.

## Component work starts with the inventory

Use `.claude/skills/component-spec-audit/SKILL.md` for any part identity, rating,
package, pin, footprint, substitution, schematic, PCB, BOM or documentation work.
Start by running its offline validator, then route exact MPN and LCSC independently
through `references/inventory.json` and read every matching owner skill.

A component owner contains the source documents, facts, conditions, pin map,
coverage and interactions. Keep unavailable evidence explicit. Do not reconstruct
missing manufacturer facts from memory or a same-name vendor part. Candidates are
separate from fitted inventory; DNP is per placement.

Use `.claude/skills/circuit-spec-integration/SKILL.md` for cross-component rails,
startup, protection, sensing, thermal, harness, configuration or as-built behavior.
Project connectivity does not prove NVM, assembled or measured state.

Adding or replacing a part follows the audit skill's
`references/new-component-workflow.md`: evidence, spec, assets, previews, generated
human reference, then validation. The component catalog under
`doc/src/content/docs/components/` is generated; never hand-edit it.

## Schematic and PCB ownership

Board P/A/B schematics are generated from `scripts/schgen/board_p_spec.py`,
`board_a_spec.py` and `board_b_spec.py`. Edit those specs and regenerate via
`gen_schematic.py`; do not
hand-edit their `.kicad_sch` outputs. See `scripts/schgen/README.md` for baseline,
decision and ERC checks. Reused board projects retain their board-local source
ownership and provenance records.

PCBs have separate layout ownership. Synchronize final component identities and
nets with the schematic, then review routing, power loops, returns, copper capacity,
thermal paths, connector orientation and mechanical clearances. Manufacturing files
must be exported from one final revision with ERC, DRC, BOM/CPL parity and explicit
remaining blockers. Do not describe incomplete routing as order-ready.

The root `zudo-pd.kicad_pro`, `zudo-pd.kicad_sch`, sheet files and `zudo-pd.kicad_pcb`
are historical and must not be regenerated from the split-board specs. Historical
orders are stored in `jlcpcb-order-snapshots/`.

## Required checks

Run appropriate tests and build steps; this hardware repository also has executable
schematic generators, component validation and a documentation application.

```sh
python3 .claude/skills/component-spec-audit/scripts/validate.py --strict
python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'
python3 .claude/skills/circuit-spec-integration/scripts/check_forward_tests.py --strict
```

Run schematic verification per `scripts/schgen/README.md` after connectivity changes.
Run `pnpm b4push` inside `doc/` after component publication or documentation changes.
A staged validator PASS may skip gates; read every printed skip and use strict mode
for final validation.

Before native STEP assembly review, run
`uv run scripts/pcb/verify-step-datums.py --output tmp/step-datum-check.json`.
The retained audit in `footprints/kicad/step-datum-verification.json` covers the reviewed active
STEP/WRL pairs. Its sampled geometry screen does not qualify physical fit. Do not
use `--normalize-reviewed` as a routine check; normalization is a separately
reviewed model mutation.

## Documentation and versioning

All documentation, diagrams, labels and comments are English. Document connectivity
with net tables (`Net | Connected pins (Ref.Pin) | Value/Note`) and Mermaid block
diagrams. Read generated specs or exported netlists, not symbol positions.

`VERSION` uses X.Y.Z: X is product release, Y is the lifetime PCBA order count, Z is
a local checkpoint. Preparing an export is not a new order. Use the existing
`.claude/skills/l-bump-version-*` workflows only when that versioning action is requested.

Repository map: `boards/` projects; `scripts/schgen/` specs and checks; `.claude/skills/`
evidence; `symbols/` and `footprints/kicad/` assets; `doc/` documentation; `3dp-files/`
the current adhesive-leg prototype and historical printed parts, including the
superseded Faston guard. `doc/CLAUDE.md` and `footprints/CLAUDE.md` provide local rules.
