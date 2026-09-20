# zudo-pd

A USB-C PD power-supply design for modular synthesizers, with a separate input board
and a synth conversion board for +12 V, −12 V and +5 V.

This is development hardware. The rail budgets are +12 V / 1.2 A, −12 V / 0.8 A and
+5 V / 0.5 A; they are targets, not measured capabilities. The renewed conversion
circuit uses AP63201, LT1963A and LT3015-12 parts with explicit headroom and thermal
qualification conditions.

Board B's screw-terminal revision is 110 × 85 mm, with two copper layers and
2 oz copper. Two top-side WJ500V-5.08-2P / C8465 blocks replace the four Fastons;
the wire entries face left. The board returns to a plain left edge and needs no
printed terminal guard. In the installed device, Board B stands on legs with its
front/component face downward. J5 is on that same front face, mating to the
face-down 27 × 40 mm Board P above B in CAD coordinates and below B when installed.
Front voltage labels remain, with normally readable duplicates on the back.
The PD module moves down to free an independent top-left support hole. All four
Ø3.0 mm corner-hole centers are 4 mm from the adjacent edges; the three Ø3.2 mm
PD mounting holes remain separate. P1 and TP3/TP4/TP5 move right together,
retaining seven top-edge contacts on 2.54 mm pitch.

See the [manufacturing guide](manufacturing/README.md) and
[corner-support review destination](manufacturing/releases/corner-support-review/) for prototype
fabrication and assembly review. The PCB is implemented and its native layout
and power-path checks pass; use the package reports for CAD and export status.
The previous front-stack package records the earlier geometry.

**HC-11's 11 mm support height does not clear this front-down assembly over a flat
floor:** the PD substrate reaches 12.7 mm and the terminal drawing maximum is
14.2 mm. The [printed adhesive leg](3dp-files/adhesive-leg/README.md) provides an
18 mm support height, a straight Ø7 mm pole and a 4.5 mm blind screw hole for
M3 × 5 mm screws through the nominal 1.6 mm PCB. See the
[support evidence](boards/board-b/supports/README.md). Physical wire fit, tightening
torque, adhesive retention, connector seating and full-load performance remain unmeasured.

**Board P requires verified 15 V-only operation.** Its new SMAJ16A-E3/61 / C968650
TVS has a 16 V standoff; factory 20 V negotiation is unsafe. First power and program
P from a current-limited 5 V-only source with B disconnected. Read back the NVM,
confirm all 20 V requests are disabled, and verify the configuration after a power
cycle before 15 V use. See the [Board P procedure](doc/src/content/docs/architecture/board-p.md).
The 26 V clamp test point and new 60 V D3 improve the conditioned stress screen;
actual surge, hot behavior and overshoot still require qualification.

## Start with the current design

- [Project brief](doc/src/content/docs/getting-started/project-brief.md)
- [Board roles and interface](doc/src/content/docs/architecture/board-contract.md)
- [Component catalog](doc/src/content/docs/components/catalog/index.mdx)
- [Component-first workflow](doc/src/content/docs/how-to/component-first-design.md)
- [Release readiness](doc/src/content/docs/architecture/release-readiness.md)
- [Historical design archive](doc/src/content/docs/archive/index.mdx)

The renewal reuses a separate Board P input module and replaces the previous synth
headers and custom printed guards with DEALON DW254P-2X8-L0 / C4749189. Exact part
records, pin maps and source evidence live in `.claude/skills/` and generate the
human-readable component catalog.

## Documentation

The [documentation site](https://pd.takazudomodular.com) uses zudo-doc, MDX and Preact.

```sh
cd doc
pnpm install
pnpm dev
```

Open `http://localhost:4321`. Run `pnpm b4push` for documentation validation.

## Design files

`boards/` holds independent board projects. `scripts/schgen/` owns generated schematic
specs and checks. `symbols/` and `footprints/kicad/` hold canonical KiCad assets.
Read [boards/README.md](boards/README.md) before editing or regenerating a board.
The [portable assembly preview](boards/board-b/assembly-preview/preview.kicad_pcb)
opens the P/B stack in KiCad for mechanical review.

**Never use Git LFS.** Large assembled STEP previews are ignored local generated
files. Their [path and hash inventory](manufacturing/local-only-assembly-previews.json)
records exactly what is omitted from Git. The combined KiCad preview, individual
component models, standalone leg STEP, printable STLs and fabrication files remain
in ordinary Git.

A fresh clone does not contain those large review assemblies. Full prototype
checksum checks and the leg's whole-assembly verification require the original
local STEP bytes; they must fail if those bytes are missing or different. See the
[manufacturing guide](manufacturing/README.md#local-assembly-previews) for generating
a new assembly review with its own source and output hashes.

The root `zudo-pd.kicad_*` project and `jlcpcb-order-snapshots/` preserve the old
combined-board orders and their evidence. The [printed accessories](3dp-files/README.md)
contain the current adhesive legs. Only the latest renewal PCB, prototype outputs
and leg design are maintained; no renewal hardware has been released or ordered.
