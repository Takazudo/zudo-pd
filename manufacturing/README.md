# Fabrication review package

[Current state](../doc/src/content/docs/project/current-state.md) owns implementation, dated checks, actual
procurement/physical state and remaining work. [Variant designs](../doc/src/content/docs/architecture/index.mdx)
and [release gates](../doc/src/content/docs/architecture/release-readiness.md) own responsibilities and acceptance.

Valid development pairs are **PD15 `board-p15 + board-b`** and **PD20 `board-p + board-b20-draft`**.
Current `board-p` is 20 V r3. P15 is shared 15 V / 3 A hardware for LED first, then PD15.
The detailed screw-terminal, leg and AP63201/LM2596/LDO material below is **PD15-specific**;
PD20 has its own [status/disposition](pd20-status.md) and four-layer B20 contract.

`releases/corner-support-review/` is a **fixed P15+B snapshot**, manifest base `3b9821b`.
The [2026-11-03 order packet](p15-order-decision-packet.md) records matching source checks at `5a21ab9`,
151/151 checksums and full independent-verifier PASS with the original local-only STEP. Preserve those results.
They do not verify current HEAD. The verifier compares against its working tree; historical replay needs matching
source hashes plus that original required STEP. This documentation work does not replay or regenerate the package.
Its older `manufacturing/README.md` source hash remains an intentional historical boundary as this guide evolves.

Received Board B matches the S3 factory BOM (`f25194f`), with full fabrication identity, LED2 rotation,
usable quantity and D1 inspection incomplete. Development C11/R21/R27 substitutions do not describe received S3.
The two-P15 plan is not an executed order; no physical programming/readback acceptance is recorded.

## Narrative classification and reading order

| Document | Classification / stream |
| --- | --- |
| [README](README.md), [package notes P15](package-notes-p15.md), [package notes B20](package-notes-b20.md) | Current technical/reference guidance; exact package scope and blockers |
| [PD20 status](pd20-status.md) | Current technical/reference disposition plus dated verification receipts; original 269-component receipt retained separately from current 270 source |
| [P15 order decision](p15-order-decision-packet.md) | Revision-specific verification/order-decision record, 2026-11-03; plan, not receipt of an order |
| [P15 order handoff](p15-order-handoff.md) | Owner order-day checklist for 2 × P15, 2026-11-08: exact files, preview checks, stock re-check, arrival tests; not an order |
| [Shared P15 reference](../boards/board-p15/shared-reference.json) | Source identity record (paths, hashes, commits, consumers); checked by `scripts/pcb/board-p15/verify-shared-reference.py`; byte identity only |
| [As-built identity and controllers](as-built-and-controller.md) | Revision-specific received identity/LED observations plus controller research; LED measurements only |
| [Board B unpowered check](board-b-unpowered-check.md) | Current procedure for received PD15 Board B D1, not an executed result |
| [Independent B20 review](pd20-b20-layout-review.md) | Original revision-specific review; findings preserved, later disposition in PD20 status |
| [PD A/B readiness](pd-ab-readiness.md), [B20 draft chronology](board-b-20v-switcher-direct-draft.md) | Historical development journals, retaining decisions/calculation/simulation chronology; current disposition in PD20 status |
| [Power budget](power-budget.md) | Source-locked revision-specific calculation record; old P r2 identity is historical, not a current path claim |
| [B1 gates](b1-gates.md), [design gaps](design-gaps-20v.md), [input clamp](input-clamp-fix.md), [input protection](input-protection-20v.md), [B20 protection](board-b-protection-20v.md) | Research/development screens feeding later adopted designs; preserve dated assumptions and decision chronology |
| [Supply capability](supply-capability.md), [supply alternatives](supply-alternatives.md), [OSC options](osc-supply-options.md), [supply alternatives comparison](product-comparison.md) | Research/candidate comparisons, not measured ratings |
| [Product lineup](product-lineup.md), [power limit](power-limit-60w.md), [multiport chargers](multiport-chargers.md), [heat spreader](heat-spreader-concept.md) | Research/candidate comparisons; adopted decisions explicitly scoped, other options remain unadopted |

Cost and stock snapshots retain their retrieval dates, including 2026-11-03. They are not fresh stock checks or quotes.
The [documentation map](../circuit/DOCUMENTATION_MAP.md) inventories every retained document and constraint.

## Generate files from checked sources

### Local assembly previews

Large `populated-stack.step` and `installed-assembly.step` files are local-only
generated previews. Git LFS is prohibited. The
[omission inventory](local-only-assembly-previews.json) records the four current paths
and three distinct assembled objects, with sizes and expected hashes. The fourth is the
board-p15 draft stack in `boards/board-b/assembly-preview-p15/`. Local copies
are retained and ignored. Component
models, native KiCad previews, printable STLs, Gerbers, drills, BOMs and CPLs
remain tracked.

The active Board B assembly preview, current prototype package and printed-leg
assembly each omit their large assembled STEP from Git. Their reports still
identify the expected local bytes. Full verification therefore requires those
local files; a fresh clone alone is not a complete mechanical review. Checks
continue to reject a missing or changed required file.

For a new current-board assembly review on the documented macOS KiCad setup,
use a new output directory:

```sh
uv run scripts/pcb/export-assembly-preview.py --output tmp/local-assembly-preview --kicad-cli /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
```

This writes new STEP and verification outputs. STEP creation timestamps mean
these are not byte-identical replacements for the existing assemblies. The leg's
existing verifier requires its original local assembly hash; it has no override
for substituting a newly generated assembly. Preserve that check and establish
new verification separately when revising the design.

### New fabrication export

When an export is separately requested, use a new destination and explicit pair:

```sh
python3 scripts/pcb/export-jlcpcb.py tmp/pd15-review --boards board-p15 board-b
python3 scripts/pcb/export-jlcpcb.py tmp/pd20-review --boards board-p board-b20-draft
```

The retired `--boards board-p board-b` pair is rejected. Exporting does not order or release anything.
See [package preparation](../doc/src/content/docs/project/jlcpcb-package.md) for native-tool requirements,
independent verification, `--write` only on a fresh export and fixed-package replay limitations.
Never refresh the fixed P15 package's source locks/checksums merely because HEAD changes.

## Fabrication and assembly

- Two copper layers, 1.6 mm FR-4. P15 uses the 27 × 40 mm module and mounting geometry, with updated TVS lands.
- Board B is 110 × 85 mm with three top fiducials and 0.07 mm (2 oz) outer copper; power-current and thermal limits still require
  measurement on the assembled prototype.
- DEALON DW254P-2X8-L0 C4749189 at J10/J11 replaces the custom printed socket guards.
  It is a right-angle through-hole header, not an SMT-only assembly item. Confirm
  the applicable wave/through-hole assembly process and exact supplier footprint
  orientation in JLCPCB's placement review.
- J6/J7 are top-side WJ500V-5.08-2P / C8465 two-pole screw-terminal blocks with
  wire entries facing left. J6.1=GND, J6.2=−12 V, J7.1=+5 V and J7.2=+12 V.
  Verify actual wire-entry orientation, pin numbering and termination against the
  exact component record and assembly drawing. J8/J9 are retired.
- The left edge is plain. No printed terminal guard is required. The current
  [printed accessory](../3dp-files/README.md) is the adhesive leg.
- P1 and TP3/TP4/TP5 form seven top-edge contacts at 2.54 mm pitch and y=1.8 mm:
  ATT, PDOK, GND, NC, +13.44 V PRE, +6.519 V PRE, −14.145 V PRE. Use P1.3 as the
  shared measurement return. The NC contact stays unconnected. The complete row
  shifts 20 mm right, with contact centers x=56.19–71.43 mm, beyond the PD module.
- Board B's J5 female header is on F.Cu. The PD module faces it from above B in
  CAD coordinates, with P's component face down and its front plane nominally at
  Z=+11.1 mm. When B is installed front-down on legs, P is physically below B.
  Map P's XY coordinates with `pd_to_board_b(x,y)=(y−0.5,x+12)` for all holes and
  mating pads. P projects to x=−0.5–39.5 mm, y=12–39 mm; J5 is at (37.2,24.9).
  The nominal plane spacing does not establish actual seated header height.
- The three PD holes remain Ø3.2 mm. Four independent HC-11 holes H4–H7 are
  Ø3.0 mm NPTH at (106,4), (4,81), (106,81) and (4,4), respectively. All four
  corner centers are 4 mm from adjacent edges. These board-only holes and the
  separately installed supports are excluded from the electrical BOM and CPL.
- Keep the front screw-terminal labels and their B.SilkS duplicates. Back labels
  must read normally when viewed from the back. Check each label against its actual
  electrical pin after changing sides in the viewer.
- Check leg height, P/B component clearance, wire access and front-edge probe access
  in the installed orientation. Use the final populated assembly, including the
  modeled maximum terminal tails, when selecting mechanical spacing.
- Socket pins 1/2 carry −12 V; verify the actual ribbon red stripe and keyed shell
  before plugging in a module. The sockets and screw terminals share each board-level rail budget.
- CPL uses native KiCad Cartesian coordinates with a common drill/place origin.
  Do not negate Y again. Rotations are native KiCad angles and still need the
  exact-part JLCPCB placement preview check.

## Printed legs and retained support evidence

The selected [printed leg](../3dp-files/adhesive-leg/README.md) has an 18 mm seating
height, 14 × 14 × 2 mm base and straight Ø7 mm pole. Its exact 27-vertex M3 profile
forms a 4.5 mm blind bore with no larger lower cavity. Start with an M3 × 5 mm
screw; through the 1.6 mm PCB it inserts 3.4 mm, leaving 1.1 mm nominal blind-floor
clearance. Do not use the earlier M3 × 8 mm recommendation. Existing Ø3.0 mm PCB
holes provide zero nominal diametral clearance for M3, so check actual screw
passage. Printing, screw retention and adhesive loading remain physical tests.
The four feet require a 116 × 91 mm adhesive footprint. Their CAD verification is
separate from the unchanged PCB and JLCPCB package.

The [HC-11 support record](../boards/board-b/supports/README.md) retains the exact
seller drawing. Its 11 mm dimension runs from the drawn base underside to the PCB
seating shoulder. Adhesive thickness, compression and finished bonded-floor datum
are not separately specified; do not add an assumed tape allowance. Complete head,
column and base envelopes are unavailable. The Ø6 mm Fab circle and 6.5 mm square
courtyard are layout assumptions, not supplier dimensions.

For B's component face toward a flat floor, P's back substrate plane is 12.7 mm
from B's front, already 1.7 mm beyond the nominal HC-11 floor plane. The terminal
is 14.0 mm nominal and 14.2 mm at the drawing maximum, exceeding that plane by
3.0–3.2 mm. P solder tails may extend farther. Moving P in X/Y frees the corner
but cannot resolve this vertical conflict. The selected 18 mm printed leg provides
3.8 mm nominal clearance over the terminal drawing maximum. Its model does not
qualify physical fit, retention or temperature performance. The HC-11 support
record documents that option's limitations; the printed leg has its own CAD
verification. Neither establishes physical testing of the printed accessory.

## Native 3D review

For PD15 open `boards/board-p15/board-p15.kicad_pro` or `boards/board-b/board-b.kicad_pro` with
its paired PCB. Active model references resolve through
`${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/`; no global KiCad path variable
is required. Export snapshots rebase those paths for their deeper `source/`
directory. Do not copy snapshot paths back into the active board.

The inductor L1 model is an explicitly illustrative maximum-body envelope,
7.5 × 6.85 × 3.0 mm. The exact manufacturer STEP download was unavailable. It
supports a body-clearance review, not terminal or manufacturing geometry. Some
other preview models are also illustrative; canonical land patterns and retained
component drawings remain the dimensional evidence. Active model paths, transforms
and STEP companions must match the current part selection. Model alignment does
not establish physical wire, screw, shroud or mounting fit.
PTC1/PTC2 model offsets now place their opaque bodies over the pad lands; PTC3's
centered model is retained. These catalog illustrations are not maximum-tolerance
package envelopes, so final physical clearance still needs review.
The C8465 illustration has shorter solder tails than its drawing: use the documented
4.7 mm maximum below the housing for physical clearance, not the model's 3.5 mm tail.

The [retained STEP datum audit](../footprints/kicad/step-datum-verification.json)
checks the reviewed active STEP/WRL pairs after alignment. It compares sampled surfaces in
both directions and preserves solid volume; the documented BD8 capacitor's interior
WRL faces are the narrow exception. This is a model-datum/orientation screen, not
an exact geometry proof or physical qualification. The default command below is
read-only for model assets; it writes only the requested report.

```sh
python3 scripts/pcb/check-model-paths.py boards/board-p15/board-p15-draft.kicad_pcb
python3 scripts/pcb/check-model-paths.py boards/board-b/board-b.kicad_pcb
uv run scripts/pcb/verify-step-datums.py --output tmp/step-datum-check.json
```

The historical r2 [P/B assembly preview](../boards/board-b/assembly-preview/preview.kicad_pcb)
opens both boards together in KiCad and carries local model files. Its
[verification report](../boards/board-b/assembly-preview/verification.json) identifies
the source revisions and modeled clearances. This is an interactive review copy;
it does not establish current P15 or r3 stack clearance. Use the intended variant and revision for any new review.

## Electrical qualification remains open

The intended rail targets are +12 V / 1.2 A, −12 V / 0.8 A, and +5 V / 0.5 A.
They are not measured capabilities. The renewed design uses AP63201 for the
+13.44 V intermediate rail, LM2596 stages at +6.519 V and −14.145 V, LT1963A
positive regulators, and an adjustable LT3015 (R26/R27/R28 divider, nominal −12.054 V) for the negative rail. Precision feedback
resistors and dedicated low-ESR polymer output capacitors address the previous
headroom and capacitor-evidence gaps. See `power-budget.json` and
`power-budget.md` for conditioned calculations and their assumptions.

Full-load startup, ripple, thermal coupling, hot fuse hold current, surge behavior,
and low-input-voltage operation still require qualification. The retained ADI
binary sources are manufacturer-document mirrors; independently retrieved primary
PDF text does not substitute for a missing primary binary hash in the evidence
registry. This limitation remains explicit in the component catalog.

The U4 and U8 tabs carry the negative intermediate rail. Do not bond them to ground
or to an uninsulated common heatsink with the positive regulators. Their copper
areas are isolated from system ground. Copper area alone is not a measured thermal
resistance. Use `power-layout.json` and `power-budget.json` (`power-budget-p15.json` for the board-p15 draft) for current source-locked
areas and conditioned limits. The ground report separately measures aggregate
sampled width and the largest individual run across connected copper polygons;
it does not describe one continuous corridor. Polygon connectivity and specified
ground stitches must also pass. Full-load testing must establish coupled temperatures
with the board front-down on its legs and the final terminals, wiring and enclosure; passing geometry checks does not
qualify cooling.

Board B retains vendor silkscreen-over-pad warnings; the exported silkscreen is
subtracted from the solder-mask openings. J10/J11 have intentional board-specific
silkscreen clipping at the straight edge, with their pads and body geometry
verified separately. These warnings remain in the full DRC report.
P15 J2.4 is **NC**, with RESET strapped to GND; J2.1/J2.2 have 100 kΩ pull-downs and no board pull-ups.
The jig supplies external pull-ups, at most 4.5 V and never from VREG_2V7. Follow
[Board P15 NVM Programming](../doc/src/content/docs/architecture/board-p15-programming.md) in full, including
P15-NVM-1–7, current-limited 5 V-only provisioning with both downstream boards disconnected, factory dump,
write/readback, full power-cycle/jig sequencing and configuration verification, then NVM-6 on a 20 V-capable PD test
source with no downstream board. RESET cannot be pulsed. Only an accepted module proceeds to L or B.
Regeneration of the desk binary is not physical programming/readback.

The PD15/P15 input TVS is Littelfuse SMAJ16A, paired with a 60 V
SDT5A60SA-13 catch diode at Board B D3. The specified 26 V clamp at 15.4 A,
10/1000 µs and 25 °C leaves conditional absolute-maximum margin; it is not a
universal voltage ceiling. Adapter/cable overshoot, hot behavior and protection
response remain unqualified. These files are for prototype fabrication and
assembly review, not a declaration of qualified full-load performance.

**First power and programming must use a current-limited 5 V-only source, with
Board B disconnected. Verify the 15 V-only NVM image, readback and reload before
connecting a PD-capable source.** A factory 20 V request can drive the 16 V TVS
into sustained conduction. Twenty-volt operation is unsupported **for P15**. PD20 r3 is a separate design with blocked 20 V NVM intent. Board P artwork
and source records do not prove what a supplied STUSB4500 is programmed to request.
A USB-PD source's 45 W nameplate budget does not prove successful startup under the
negative converter's input-current transient.

This workflow prepares reviewable files. It does not place or pay for an order.

## External file-format references

- [JLCPCB KiCad BOM and CPL guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad)
- [JLCPCB pick-and-place requirements](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly)
- [JLCPCB copper weight and fabrication limits](https://jlcpcb.com/help/article/jlcpcb-copper-weight)
- [Mixed SMT and through-hole assembly](https://jlcpcb.com/blog/mixed-technology-pcb-assembly-combining-smt-and-tht)
- [Exact DEALON component](https://jlcpcb.com/partdetail/DEALON-DW254P_2X8L0/C4749189)
