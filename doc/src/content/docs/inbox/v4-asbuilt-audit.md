---
title: v4 As-Built Order Verification & Footprint Geometry Audit
sidebar_position: 13
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

This page answers two separate questions about the v0.4.0 (4th JLCPCB order) hardware, both
at the **as-built / geometry** level rather than the schematic-correctness level (see
[v3 USB-PD Failure Diagnosis](./v3-pd-failure-diagnosis.md) for the schematic-level pin-18 root
cause, which a sibling page covers for v4):

- **(a)** Did the pin-18 fix and the intended BOM actually reach a real JLCPCB order for v0.4.0?
- **(b)** Do the U1 / J1 / D4 footprints have the correct physical geometry (pad position,
  rotation, mirroring) on the board — the class of bug that passes net-matching but still kills
  the board, because a footprint can be rotated 90/180° while every pad still carries the
  electrically-correct net.

**Method:** every claim below is backed by either (1) git history on files tracked in this
repo, (2) a KiCad netlist export (`__inbox/zudo-pd-netlist.xml`, geometry-free pad→net truth),
(3) direct pad coordinates read from `zudo-pd.kicad_pcb` and `footprints/kicad/*.kicad_mod`, or
(4) locally-generated JLCPCB manufacturing files recovered from the gitignored `jlcpcb/`
working directory on this machine. No KiCad GUI was used.

## (a) Did the v0.4.0 order artifacts actually get produced?

### Timeline reconstructed from git + local files

| When (JST) | Artifact | What it shows |
| --- | --- | --- |
| 2026-06-01 08:43 | commit `f69bfd3` | Schematic fix: pin 18 (VBUS_VS_DISCH) wired `VBUS_IN → R14 (470 Ω) → U1.18` |
| 2026-06-05 ~03:20 | `jlcpcb/` working dir (gitignored, found on this machine) | `kicad-jlcpcb-tools` plugin generated gerbers + BOM + CPL locally |
| 2026-06-05 03:24 | `jlcpcb/production_files/*` (mtimes) | BOM-zudo-pd.csv, CPL-zudo-pd.csv, GERBER-zudo-pd.zip written |
| 2026-06-05 03:36–03:40 | `~/Downloads/capture-2026-06-04T18_3*.png` (4 files) | Local placement-preview renders titled "zudo-PD v0.4.0" (see note below) |
| 2026-06-05 04:59 | commit `7854736` | `fix(usb-pd): v0.4.0 faston swap to C591344 + harmonize BOM comments` — schematic/PCB committed |
| 2026-06-05 05:00 | commit `2c29375` | Renamed order snapshots to X.Y.Z scheme; added `v0_3_0/` (the v3 order snapshot) — **no `v0_4_0/` was added here** |
| 2026-06-05 → 2026-07-05 | (nothing) | No further commits touch `zudo-pd.kicad_sch` / `zudo-pd.kicad_pcb`. No `*zudo-pd*gerber*BOM*` file appears anywhere under `~/Downloads` after 2026-06-05. None of the `zudo-pd-backups/*.zip` snapshots (checked 06-05, 06-13, 06-17) contain a `jlcpcb-order-snapshots` or `jlcpcb-ready` path — they are partial source-tree backups, not order archives. |

<Note title="What the capture-2026-06-04*.png screenshots actually are">

These 4 PNGs are **not** JLCPCB order-confirmation screenshots. They are placement-preview
renders with a JLCPCB-style watermark, produced locally by the `kicad-jlcpcb-tools` KiCad
plugin (see [Generate JLCPCB Files with kicad-jlcpcb-tools](../how-to/kicad-jlcpcb-tools.md)) —
the same plugin run that produced `jlcpcb/production_files/`. They show component placement for
visual sanity-checking before upload; they carry no order number, price, or "submitted"
confirmation UI. They corroborate the manufacturing-file generation step, nothing more.

</Note>

### Verdict: did the design fix reach a JLCPCB-ready package?

**Yes.** Verified two independent ways:

1. **Netlist (geometry-free, current HEAD):** net `VBUS_VS_DISCH` (net code 39) contains exactly
   `{ R14.2, TP6.1, U1.18 }`, and net `VBUS_IN` (net code 37) contains `R14.1` alongside
   `J1.A9`, `J1.B9`, `U1.24`. This confirms `VBUS_IN → R14 (470 Ω) → U1 pin 18` is wired in the
   committed schematic — the fix is real, not just described in prose.
2. **Recovered local JLCPCB export** (`jlcpcb/production_files/`, generated 2026-06-05 03:24,
   ~1.5 h before it was committed as `7854736`) contains `R14,470ohm,R0603,72.51,-6.08,0.0,top`
   in the CPL and the faston swap (`63951-1,"J6,J7,J8,J9",CONN-TH_1217754-1,C591344,4`) in the
   BOM — i.e. a JLCPCB-ready package **was** generated reflecting the fixed design.

### Verdict: was an actual v0.4.0 order placed and manufactured?

**Unrecoverable locally.** No artifact on this machine confirms the package above was ever
uploaded, quoted, or paid for at JLCPCB:

- No `jlcpcb-order-snapshots/v0_4_0/` existed before this audit (the gap this task exists to
  close).
- No gerber/BOM/CPL zip with a JLCPCB order code (the pattern seen for earlier orders is a
  hash-like folder name + `_Y<n>`, e.g. `7543760a_y33` for the v3 order, dated 2026-05-31 —
  **before** the pin-18 fix) appears anywhere under `~/Downloads` after 2026-06-05.
- No `from-order-detail`-style confirmed BOM (`bom.xls`), layout render, or product-detail photo
  exists for a v4 order, unlike v0_1_0 through v0_3_0 which all have one.
- `CLAUDE.md`'s own phase note is present-tense: *"v0.4.0 (4th JLCPCB order) — **ordering**."* —
  consistent with "package prepared, order not yet confirmed placed," not "received and tested."

**What the user must do to close this out:** log into the JLCPCB order-history page
(`https://jlcpcb.com/user/order/list` or account → Order History) and check for an order placed
on/after 2026-06-05 for this board. If one exists:

1. Download the confirmed BOM (JLCPCB's own export, showing any manufacturer-side substitutions)
   and any layout/product-detail renders from the order-detail page.
2. Drop them into `jlcpcb-order-snapshots/v0_4_0/from-order-detail/` (placeholder created by
   this audit — see below).
3. Re-run the D4/U1/R-value comparison in this doc against the confirmed BOM, not just the
   locally-generated one, since JLCPCB can silently substitute out-of-stock basic parts.

If no such order exists, v0.4.0 has **not** been manufactured yet — the fix exists only in git and the local `jlcpcb/` export, and the next actionable step is to actually place the order using the recovered files in `jlcpcb-order-snapshots/v0_4_0/used-for-order/` (below).

### BOM comparison: front-end parts

| Ref | Schematic Value / LCSC | Recovered local BOM/CPL | Verdict |
| --- | --- | --- | --- |
| U1 | STUSB4500QTR / **C2678061** | STUSB4500QTR / C2678061 | Match |
| D4 | USBLC6-2SC6 / **C7519** | USBLC6-2SC6 / C7519 | Match — see substitution-risk note below |
| R14 | 470ohm / **C23179** | 470ohm / C23179 | Match |
| R17 | 5.1k / **C23186** | 5.1k / C23186 (grouped with R18, R3) | Match |
| R18 | 5.1k / **C23186** | 5.1k / C23186 (grouped with R17, R3) | Match |
| R19 | 0 / **C21189** | 0 / C21189 (grouped with R20) | Match |
| R20 | 0 / **C21189** | 0 / C21189 (grouped with R19) | Match |

<Warning title="D4 substitution risk cannot be fully closed out locally">

The schematic and the locally-generated BOM/CPL agree on **C7519** for D4 (USBLC6-2SC6, SOT-23-6).
Net-level connectivity is also correct: D4 pins 1↔6 both sit on the CC1 group
(`Net-(J1-CC1)` / `Net-(U1-CC1)`) and pins 3↔4 both sit on the CC2 group
(`Net-(J1-CC2)` / `Net-(U1-CC2)`) — the internal flow-through joins the part needs to work at
all. **What cannot be verified from local files** is whether JLCPCB's own order pipeline
substituted a different (cheaper/in-stock) TVS array at BOM-matching time — that only shows up
in the from-order-detail confirmed BOM, which does not exist locally (see above). If a
substitute lacks the same 1↔6 / 3↔4 flow-through internal wiring, CC sensing silently breaks
even though every design file looks correct. Check the confirmed order BOM for D4's LCSC number
once recovered.

</Warning>

<Note title="A residual BOM-harmonization gap found in the recovered export">

Commit `7854736`'s stated goal was to harmonize R13/R14 (both 470 Ω, both LCSC `C23179`) so they
collapse into one BOM row. The **schematic** does have both at `Value = "470ohm"` (verified
directly in `usb-pd-input.kicad_sch`). However the **recovered local export**
(`jlcpcb/production_files/BOM-zudo-pd.csv`) still lists them as two separate rows —
`470,R13,R0603,C23179,1` and `470ohm,R14,R0603,C23179,1` — because the `kicad-jlcpcb-tools`
plugin caches its own per-component "value" override in `project.db`
(`part_info` table: `R13|470|...` vs `R14|470ohm|...`), and that cache was not refreshed after
the schematic edit. This is harmless for ordering (both still resolve to the same LCSC part,
just as two BOM lines instead of one) but means the harmonization commit's own goal was not
fully realized in what was actually exported. If/when regenerating manufacturing files for a
real order, re-run the plugin's value sync (or manually edit the R13 row) first.

</Note>

### `jlcpcb-order-snapshots/v0_4_0/` scaffold

Created, mirroring the `v0_3_0/` layout:

```
jlcpcb-order-snapshots/v0_4_0/
├── used-for-order/
│   ├── BOM-zudo-pd.csv     ← recovered from gitignored jlcpcb/production_files/, 2026-06-05 03:24
│   ├── CPL-zudo-pd.csv     ← same
│   └── GERBER-zudo-pd.zip  ← same
└── from-order-detail/
    └── README.md           ← placeholder; nothing to recover locally (see verdict above)
```

The `used-for-order/` files are **not** placeholders — they are the actual locally-generated
manufacturing package recovered from this machine's gitignored `jlcpcb/` directory (per the
"Repository Convention" section of
[Generate JLCPCB Files with kicad-jlcpcb-tools](../how-to/kicad-jlcpcb-tools.md), that directory
is meant to be copied into `jlcpcb-order-snapshots/` for exactly this reason, and never was for
v0.4.0). `from-order-detail/` only gets a `README.md` placeholder, since the manufacturer-side
confirmation cannot be recovered from local files — it requires the JLCPCB account lookup
described above.

## (b) Footprint geometry audit

Net-level pad→net matching for U1, J1, D4 was already verified correct at plan time
(re-confirmed above via `__inbox/zudo-pd-netlist.xml`). Net matching is number-based, though —
it cannot detect that a footprint is drawn/placed correctly. All geometry below is computed
directly from `(at ...)` values in `zudo-pd.kicad_pcb` and the pad list in the corresponding
`footprints/kicad/*.kicad_mod` library file.

### U1 — QFN-24 (STUSB4500QTR)

Board placement (`zudo-pd.kicad_pcb`): `(footprint "zudo-pd:QFN-24_L4.0-W4.0-P0.50-BL-EP2.8" (layer "F.Cu") (at 44.9 12.9 180))`
— top side (not mirrored to `B.Cu`), rotated 180°.

Library footprint (`footprints/kicad/QFN-24_L4.0-W4.0-P0.50-BL-EP2.8.kicad_mod`), local/unrotated
frame:

- Pad 1: `(at -1.25 2.00)`; pin-1 dot marker `fp_circle (center -2.00 2.00)` on `F.Fab`.
- Pads 1–6 run along the local `y = +2.00` edge (west→east), 7–12 along `x = +2.00`
  (south→north), 13–18 along `y = -2.00` (east→west), 19–24 along `x = -2.00` (north→south) —
  i.e. numbering proceeds **counter-clockwise** in the footprint's own frame, viewed top-down as
  KiCad renders it. This matches the issue's stated DS12499 QFN-24 convention (CCW numbering,
  pin-1 corner marker).

Absolute board coordinates after the 180° placement rotation (`(x,y) → (-x,-y)` for a pure 180°
rotation, then translate by `(44.9, 12.9)`):

- **Pad 1 center: (46.15, 10.90) mm**
- **Pin-1 dot marker: (46.90, 10.90) mm**

Since 180° is a pure rotation (no mirror flag, layer stays `F.Cu`), it preserves chirality —
the CCW pad numbering survives placement, so this is not a mirrored footprint.

<Tip title="Independently confirmed by this project's own JLCPCB tooling history">

`zudo-pd.kicad_pcb`'s raw rotation for U1 (180°) is **not** what gets sent to JLCPCB — and that
mismatch is expected, not a bug. [Generate JLCPCB Files with kicad-jlcpcb-tools](../how-to/kicad-jlcpcb-tools.md)
documents that PCBA v2 hit exactly this failure mode (U1 placed at 180° in the CPL when JLCPCB's
library expected 270°; JLCPCB's pre-production review caught it), and that the project's
`kicad-jlcpcb-tools` correction rule for this footprint (`QFN-24_L4.0-W4.0-P0.50-BL-EP2.8` → +270°,
displayed as CPL rotation `90`) was confirmed correct by JLCPCB during that review. The
**locally recovered v0.4.0 CPL** (`jlcpcb-order-snapshots/v0_4_0/used-for-order/CPL-zudo-pd.csv`)
shows exactly this expected, previously-confirmed value:

```
U1,STUSB4500QTR,QFN-24_L4.0-W4.0-P0.50-BL-EP2.8,44.9,-12.9,90.0,top
```

**Verdict: correct**, backed by (1) independent geometry computation above, (2) this project's
own documented JLCPCB-confirmed correction rule, and (3) the actual recovered v0.4.0 export
carrying that exact corrected value.

</Tip>

### J1 — USB-C receptacle (TYPE-C-SMD_TYPE-C-6P)

Board placement: `(at 44.68 4.6 180)`, layer `F.Cu` (top, not mirrored).

Library footprint pads (local/unrotated, single row at `y = -2.03`):
`B12 (-2.70,-2.03)`, `B9 (-1.50,-2.03)`, `A5 (-0.50,-2.03)`, `B5 (0.50,-2.03)`,
`A9 (1.50,-2.03)`, `A12 (2.70,-2.03)`.

After the 180° placement rotation and translation:

| Pad | Local (x,y) | Absolute (x,y) mm |
| --- | --- | --- |
| A5 (CC1) | (-0.50, -2.03) | **(45.18, 6.63)** |
| B5 (CC2) | (0.50, -2.03) | **(44.18, 6.63)** |
| A9 (VBUS) | (1.50, -2.03) | **(43.18, 6.63)** |
| B9 (VBUS) | (-1.50, -2.03) | **(46.18, 6.63)** |

180° is a pure rotation (no `B.Cu`/mirror), so this is not a mirrored footprint — it is a
regular end-for-end rotation of a single-row connector. Netlist-confirmed: `A9` and `B9` are
both tied to net `VBUS_IN` (already electrically redundant — a residual left/right ambiguity in
which physical VBUS tab is A vs B is a non-issue), and `A5`/`B5` (CC1/CC2) each go through the
D4 ESD array to the STUSB4500's dedicated CC1/CC2 pins, which is exactly what the flip-detection
scheme on this chip is designed to tolerate. No functional risk identified from the rotation
value itself; the how-to guide for this project's JLCPCB tooling does not list
`TYPE-C-SMD_TYPE-C-6P` among the footprints needing a rotation-correction override, and the
recovered CPL leaves J1 at rotation `180.0`, unchanged from the raw board value — consistent
with "no correction needed" for this connector family.

### D4 — SOT-23-6 (USBLC6-2SC6)

Board placement: `(at 51.65 11.75)` — **no rotation specified (0°)**, layer `F.Cu` (top, not
mirrored). This is the lowest-risk placement of the three: no transform is applied at all, so
the library footprint's own layout passes straight through to the board.

Library footprint pads (`footprints/kicad/SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL.kicad_mod`):

| Pad | Local (x,y) | Absolute (x,y) mm |
| --- | --- | --- |
| 1 | (-0.95, 1.15) | **(50.70, 12.90)** |
| 2 | (0.00, 1.15) | **(51.65, 12.90)** |
| 3 | (0.95, 1.15) | **(52.60, 12.90)** |
| 4 | (0.95, -1.15) | **(52.60, 10.60)** |
| 5 | (0.00, -1.15) | **(51.65, 10.60)** |
| 6 | (-0.95, -1.15) | **(50.70, 10.60)** |

Pads 1-2-3 run one edge west→east, pads 4-5-6 run the opposite edge east→west (4 opposite 3, 6
opposite 1) — the standard SOT-23-6 perimeter pattern, matching the datasheet pinout given in
the issue (1=I/O1, 2=GND, 3=I/O2, 4=I/O2, 5=VBUS, 6=I/O1). The pin-1 marker
(`fp_circle (center -1.46 1.40)` on `F.Fab`, plus a silkscreen circle) sits directly next to pad
1 at the correct corner. Combined with the netlist confirmation (pins 1↔6 both on the CC1
group, 3↔4 both on the CC2 group, pin 5 on VBUS_IN, pin 2 on GND — see substitution-risk note
above), and the project's own JLCPCB-tooling gotcha guide (`kicad-jlcpcb-tools.md`) documenting
that this exact footprint needs **rotation = 0** as an override to a default plugin rule that
would otherwise mis-rotate it by -90° — which the recovered CPL confirms
(`D4,USBLC6-2SC6,SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL,51.65,-11.75,0.0,top`) — **verdict: correct.**

## Summary

| Item | Verdict |
| --- | --- |
| Pin-18 fix (`VBUS_IN → R14 → U1.18`) reached committed design files | Yes (netlist-verified) |
| Pin-18 fix reached a JLCPCB-ready local export | Yes (recovered `jlcpcb/` dir, 2026-06-05) |
| A real v0.4.0 order was placed/manufactured at JLCPCB | Unrecoverable locally — check JLCPCB order history for post-2026-06-05 activity |
| U1/D4/R14/R17-R20 LCSC parts match between schematic and local BOM | Match (see table) |
| D4 substitution risk at JLCPCB's own BOM-matching step | Cannot be ruled out locally — verify against confirmed order BOM once recovered |
| R13/R14 BOM-row harmonization | Done in schematic; **not** reflected in the locally-exported BOM due to a stale plugin cache |
| U1 (QFN-24) footprint geometry/rotation | Correct — matches this project's own JLCPCB-confirmed correction (270°/CPL "90") |
| J1 (USB-C) footprint geometry/rotation | Correct — pure 180° rotation, not mirrored, no correction needed for this connector family |
| D4 (SOT-23-6) footprint geometry/rotation | Correct — zero-rotation passthrough, matches required override for this footprint family |
| `jlcpcb-order-snapshots/v0_4_0/` gap | Closed — `used-for-order/` populated with recovered files, `from-order-detail/` placeholder + instructions added |
