# Fabrication review package

The active design pairs the reusable 27 × 40 mm **Board P** USB-PD module with
**Board B**, the synth conversion and distribution board. The older Board A and
root v4 project remain historical references.

The compact prototype files are generated and locally verified in
`compact-review`, including the fully routed 110 × 95 mm Board B. Its source-locked
reports establish the final file-check state. The earlier
`renewal-review` package describes the 150 × 115 mm board; it is not interchangeable
with the compact fabrication data.

## Generate files from checked sources

```sh
python3 scripts/pcb/export-jlcpcb.py manufacturing/releases/compact-review
uv run --with gerbonara --with resvg-py python scripts/pcb/verify-jlcpcb.py manufacturing/releases/compact-review
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
- Board B is 110 × 95 mm with three top fiducials and 0.07 mm (2 oz) outer copper; power-current and thermal limits still require
  measurement on the assembled prototype.
- DEALON DW254P-2X8-L0 C4749189 at J10/J11 replaces the custom printed socket guards.
  It is a right-angle through-hole header, not an SMT-only assembly item. Confirm
  the applicable wave/through-hole assembly process and exact supplier footprint
  orientation in JLCPCB's placement review.
- The Faston blades face outward from Board B's left edge. P1 sits at the top
  edge for pogo access. Check the actual female terminal housings and programming
  jig envelope; bare component models do not establish those mating clearances.
- Board B's J5 female header is on the bottom; Board P's JOUT1 male is on the top.
  Their pins and three mounting-hole centers must align in the same XY frame.
  Select final standoff length by checking actual mating depth and component
  clearance; nominal header body height alone does not establish it.
- Socket pins 1/2 carry −12 V; verify the actual ribbon red stripe and keyed shell
  before plugging in a module. The two output sockets share the board rail budget.
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
component drawings remain the dimensional evidence. The USB and Faston model
transforms have been corrected to their footprints.

```sh
python3 scripts/pcb/check-model-paths.py boards/board-p/board-p.kicad_pcb
python3 scripts/pcb/check-model-paths.py boards/board-b/board-b.kicad_pcb
```

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
resistance. The compact layout has less connected heat-spreading copper around
U8 than the larger board. Use `power-layout.json` and `power-budget.json` for the
current source-locked areas and conditioned limits. Full-load testing must establish
coupled temperatures; passing the geometric checks does not qualify cooling.

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
