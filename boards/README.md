# Board projects

The renewed design separates the USB-PD input module from synth conversion.

| Project | Role | Source ownership |
| --- | --- | --- |
| `board-p/` | Reusable USB-PD input module | Schematic generated from `scripts/schgen/board_p_spec.py`; routed PCB and `mechanical.json` own the geometry |
| `board-a/` | Previous USB-PD input-board design | Generated from `scripts/schgen/board_a_spec.py` |
| `board-b/` | Synth conversion, protection and output connectors | Schematic generated from `scripts/schgen/board_b_spec.py`; PCB has separate layout ownership |

The root combined-board KiCad files remain the historical v0.4.0 reference.
Use the [current architecture](../doc/src/content/docs/architecture/board-contract.md)
for interface roles and the [release gates](../doc/src/content/docs/architecture/release-readiness.md)
before exporting an order package.

Board B's screw-terminal revision is 110 × 85 mm with two copper layers,
2 oz outer copper and 76 schematic components. Two top-side WJ500V-5.08-2P / C8465 blocks have wire entries
facing left. J6 carries GND/−12 V and J7 carries +5 V/+12 V. J8/J9 are retired.
The active board has a plain left edge and requires no printed terminal guard.

Board B is installed on legs with its front/component face down. J5 now sits on
F.Cu with the other components. Board P faces that front surface: its component
face points down in CAD, with its front plane nominally at Z=+11.1 mm relative to
B's front plane. This places P physically below B in the installed orientation.
The mapping `pd_to_board_b(x, y) = (y−0.5, x+12)` transforms P's three mounting holes and
all six J5 mating pads together. Board P's own PCB is unchanged. Placement and
transform ownership is `scripts/pcb/board_b_layout.py`.
The P projection is x=−0.5–39.5 mm, y=12–39 mm, leaving B's top-left corner free.
J5 is at (37.2,24.9), 270°. PD holes H1/H2/H3 are Ø3.2 mm at (3.5,16),
(3.5,35) and (32.1,24.8).

The independent HC-11 corner holes H4/H5/H6/H7 are Ø3.0 mm NPTH at (106,4),
(4,81), (106,81) and (4,4), respectively. All four centers are 4 mm from the
adjacent edges. These are board-only holes; supports are separately procured
mechanical accessories, excluded from the electrical BOM and placement output.
The [support evidence](board-b/supports/README.md) retains the exact drawing and
its missing head/base envelopes. HC-11's 11 mm support height does not clear the
front-down assembly above a flat floor: P's substrate reaches 12.7 mm and the
terminal drawing maximum is 14.2 mm. The selected
[18 mm printed-leg prototype](../3dp-files/adhesive-leg/README.md) addresses that
nominal height conflict with separate CAD verification. It leaves the PCB and
JLCPCB package unchanged. Check actual M3 passage through the existing Ø3.0 mm
holes, printed fit, screw retention and adhesive loading. Its four bases require
a 116 × 91 mm adhesive footprint. Frozen support reports retain the earlier
HC-11 assumption.

Both front and back carry the screw-terminal voltage labels. Back labels use
B.SilkS mirroring so they read normally when viewed from the back. Validate them
against the same four electrical pins; changing the viewing side does not change
the pin assignments. Select leg and stack spacing from the populated assembly.

P1 plus TP3/TP4/TP5 retains a seven-contact top-edge row on 2.54 mm pitch at y=1.8 mm,
shifted 20 mm right to x=56.19–71.43 mm. Its voltage legend is centered at (88,2).
P1.3 is the shared probe ground; P1.4 remains NC. See the
[board contract](../doc/src/content/docs/architecture/board-contract.md) for exact pins.
The [corner-support review destination](../manufacturing/releases/corner-support-review/)
and [manufacturing guide](../manufacturing/README.md) track the current prototype.
The PCB is implemented and native layout and power-path checks pass; package
reports determine CAD and export status. Physical wire fit, tightening
torque, support clearance and retention, connector seating and full-load behavior
remain unmeasured. The previous front-stack board is retained under
`board-b/archive/110x85-front-stack/` and in its immutable review package.

The old guard and T-notch contract remain in the [3D-print archive](../3dp-files/README.md).
Preserve those source files and earlier release packages; do not apply their
notched edge or underside Faston placement to the active board.

Board P D5 is now Vishay SMAJ16A-E3/61 / C968650, with a 16 V standoff. **20 V
negotiation is unsafe.** First power and program P at 5 V only with B disconnected;
read back the NVM, disable every 20 V request and verify the 15 V-only policy after
a power cycle before connecting a higher-voltage-capable PD source. Follow the
[Board P procedure](../doc/src/content/docs/architecture/board-p.md).
Board B D3 is SDT5A60SA-13 / C3024223, rated 60 V reverse. The conditioned 26 V / 25 °C
clamp screen clears the former table-point mismatch; installed surge and thermal
performance remain open.

## Generated schematics

Edit the spec, then regenerate the schematic; do not hand-edit generated output:

```sh
python3 scripts/schgen/gen_schematic.py board_p_spec
python3 scripts/schgen/gen_schematic.py board_a_spec
python3 scripts/schgen/gen_schematic.py board_b_spec
```

See `scripts/schgen/README.md` for baseline, decision and ERC verification. The
component audit must remain in parity with the exact generated MPN/LCSC/footprint
placements. A PCB change must be checked against that final schematic.

## Libraries resolve from each board directory

For projects two levels below the repository root, shared library references use:

```text
${KIPRJMOD}/../../symbols/zudo-pd.kicad_sym
${KIPRJMOD}/../../footprints/kicad/zudo-power.pretty
```

Open the paired `.kicad_pro` project in its board directory. Active 3D model paths
use `${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/`; no global KiCad model
path setup is required. Export snapshots use rebased paths for their deeper
`source/` directory, which must not be copied back into the active board. Verify
both active boards with `scripts/pcb/check-model-paths.py` before exporting.
The [STEP datum audit](../footprints/kicad/step-datum-verification.json) checks
the reviewed active STEP/WRL pairs. Re-run it with `uv run scripts/pcb/verify-step-datums.py`;
its sampled surface comparison establishes model consistency, not physical fit.
L1's visible model is an illustrative maximum-body envelope, not an exact
manufacturer model; see the [manufacturing guide](../manufacturing/README.md).
The [portable P/B assembly preview](board-b/assembly-preview/preview.kicad_pcb)
shows the complete stack with local model files. It is a review copy, not the
manufacturing PCB; retain its verification report when sharing it.

Check a project's own library tables when importing a reusable module. Package names,
pad numbers, model paths and connector pin assignments must resolve in this repository.

## Connector and mounting changes

Board B J10/J11 use DEALON DW254P-2X8-L0 / C4749189 with the conventional synth power
pin map (pins 1–2 = −12 V). The shroud replaces custom printed guards. Derive edge
clearances from the actual connector body and mating cable; do not inherit the old
printed-part contour. Board P's mounting geometry belongs to its PCB source and
mechanical record, not to assumptions about the previous Board A design.
