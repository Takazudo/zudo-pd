# Fabrication review package

The active design pairs the reusable 27 × 40 mm **Board P** USB-PD module with
**Board B**, the synth conversion and distribution board. The older Board A and
root v4 project remain historical references.

The 110 × 85 mm screw-terminal prototype package is locally verified in
`terminal-review`; its reports bind the checks to the recorded source revision.
Physical wire fit, tightening torque, stack fit and full-load qualification remain
open. Earlier `guarded-review`,
`compact-review` and `renewal-review` packages are immutable records of older geometry;
do not use them to fabricate the current revision.

## Generate files from checked sources

```sh
python3 scripts/pcb/export-jlcpcb.py manufacturing/releases/terminal-review
uv run --with gerbonara --with resvg-py python scripts/pcb/verify-jlcpcb.py manufacturing/releases/terminal-review
```

Use `--boards board-p` to export the PD module alone. Output directories must be
new. The exporter refuses missing PCB files, PCB/schematic/registry differences,
DRC errors, unrouted connections, and ERC errors. It preserves intentional DNP
parts and excludes bare test pads and mounting holes from both BOM and CPL.

Each board folder contains a Gerber/drill ZIP, `bom.csv`, `cpl.csv`, excluded-part
list, schematic PDF, assembly drawings, source snapshot, and full check reports.
The package also includes the power budget and source-locked filled-copper geometry report.
The manifest locks source and exported artifact hashes. Review drawings and warnings alongside the manufacturing
files. An electrically unqualified prototype does not become qualified by passing
DRC, ERC, or a file-format check.

## Fabrication and assembly

- Two copper layers, 1.6 mm FR-4. Board P reuses the 27 × 40 mm routed module and mounting geometry, with updated TVS lands.
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
- The left edge is plain. No printed terminal guard is required. The earlier
  [Faston guard](../3dp-files/README.md) and its notched PCB contract are historical.
- P1 and TP3/TP4/TP5 form seven top-edge contacts at 2.54 mm pitch and y=1.8 mm:
  ATT, PDOK, GND, NC, +13.44 V PRE, +6.519 V PRE, −14.145 V PRE. Use P1.3 as the
  shared measurement return. The NC contact stays unconnected.
- Board B's J5 female header is on the bottom; Board P's JOUT1 male is on the top.
  The P stack rotates in-plane under B's upper left. Apply `pd_to_board_b` to all
  mating pads and the three holes together; the boards no longer use identical
  local XY coordinates. Board P's own PCB is unchanged. Select final standoffs by
  checking actual mating depth and component clearance.
- Socket pins 1/2 carry −12 V; verify the actual ribbon red stripe and keyed shell
  before plugging in a module. The sockets and screw terminals share each board-level rail budget.
- CPL uses native KiCad Cartesian coordinates with a common drill/place origin.
  Do not negate Y again. Rotations are native KiCad angles and still need the
  exact-part JLCPCB placement preview check.

## Native 3D review

Open `boards/board-p/board-p.kicad_pro` or `boards/board-b/board-b.kicad_pro` with
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
The C8465 illustration has shorter solder tails than its drawing: use the documented
4.7 mm maximum below the housing for physical clearance, not the model's 3.5 mm tail.

The [retained STEP datum audit](../footprints/kicad/step-datum-verification.json)
checks the reviewed active STEP/WRL pairs after alignment. It compares sampled surfaces in
both directions and preserves solid volume; the documented BD8 capacitor's interior
WRL faces are the narrow exception. This is a model-datum/orientation screen, not
an exact geometry proof or physical qualification. The default command below is
read-only for model assets; it writes only the requested report.

```sh
python3 scripts/pcb/check-model-paths.py boards/board-p/board-p.kicad_pcb
python3 scripts/pcb/check-model-paths.py boards/board-b/board-b.kicad_pcb
uv run scripts/pcb/verify-step-datums.py --output tmp/step-datum-check.json
```

The combined [P/B assembly preview](../boards/board-b/assembly-preview/preview.kicad_pcb)
opens both boards together in KiCad and carries local model files. Its
[verification report](../boards/board-b/assembly-preview/verification.json) identifies
the source revisions and modeled clearances. This is an interactive review copy;
export fabrication files from the active board projects.

## Electrical qualification remains open

The intended rail targets are +12 V / 1.2 A, −12 V / 0.8 A, and +5 V / 0.5 A.
They are not measured capabilities. The renewed design uses AP63201 for the
+13.44 V intermediate rail, LM2596 stages at +6.519 V and −14.145 V, LT1963A
positive regulators, and LT3015-12 for the negative rail. Precision feedback
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
resistance. Use `power-layout.json` and `power-budget.json` for current source-locked
areas and conditioned limits. The ground report separately measures aggregate
sampled width and the largest individual run across connected copper polygons;
it does not describe one continuous corridor. Polygon connectivity and specified
ground stitches must also pass. Full-load testing must establish coupled temperatures
with the final terminals, wiring and enclosure; passing geometry checks does not
qualify cooling.

Board B retains vendor silkscreen-over-pad warnings; the exported silkscreen is
subtracted from the solder-mask openings. J10/J11 have intentional board-specific
silkscreen clipping at the straight edge, with their pads and body geometry
verified separately. These warnings remain in the full DRC report.
Board P's reused pogo artwork has application-specific label corrections:
J2.4 is `RST` (RESET), J3.4 is `VBUS`, and J3.5 is `GND`. Their electrical pinout
is unchanged; library-mismatch warnings retain this intentional artwork difference.

The renewed input TVS is Vishay SMAJ16A-E3/61, paired with a 60 V
SDT5A60SA-13 catch diode at Board B D3. The specified 26 V clamp at 15.4 A,
10/1000 µs and 25 °C leaves conditional absolute-maximum margin; it is not a
universal voltage ceiling. Adapter/cable overshoot, hot behavior and protection
response remain unqualified. These files are for prototype fabrication and
assembly review, not a declaration of qualified full-load performance.

**First power and programming must use a current-limited 5 V-only source, with
Board B disconnected. Verify the 15 V-only NVM image, readback and reload before
connecting a PD-capable source.** A factory 20 V request can drive the 16 V TVS
into sustained conduction. Twenty-volt operation is unsupported. Board P artwork
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
