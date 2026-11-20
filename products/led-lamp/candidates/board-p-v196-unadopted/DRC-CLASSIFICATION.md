# V196 native DRC rerun and classification of the 22 findings

**Result: FAIL (exit 5) against the active board rules — 22 findings, identical to the
original V196 run and to V148.** Regression-equal, not DRC PASS. No threshold was
relaxed, no exclusion added, no zone fill run, no geometry changed.

## Rerun receipt (2026-10-31)

| Item | Value |
| --- | --- |
| Tool | `kicad-cli version` = `10.0.6`, image `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec` (pulled via mirror.gcr.io) |
| Container | `--network none --cpus 2 --memory 6g`, serialized with `flock /tmp/kicad-native.lock`, outer `timeout 600` |
| Input | byte copy of this directory's 22 candidate files; hashes before = after (`evidence/rerun-20261031/INPUT-HASHES.before.txt`); KiCad only created a `.kicad_prl` (gitignored, excluded) |
| Primary command | `kicad-cli pcb drc --format json --severity-all --units mm --exit-code-violations -o V196-rerun-drc.json board-p-COUT1206-TRIAL.kicad_pcb` |
| Exit | 5; "Found 22 violations, Found 0 unconnected items" |
| Output | `evidence/rerun-20261031/V196-rerun-drc.json` SHA256 `69d2961e58d991d38b3282ed19109a40a03e5e83d2f3e3b3ca80834ab00ecf3d` |
| Comparison | vs original `evidence/original-v196-native/V196-drc.json` (SHA256 `8ed420f3…ac51e4`): all 22 records equal on type, severity, description (incl. numeric values), item descriptions, UUIDs and positions; ignored checks, included severities, version, units, unconnected and schematic-parity arrays equal |

The original run's exact command line was not transferred (its `CONFIG.json` /
`EXECUTION-MANIFEST.json` are listed only by hash). The flags above were chosen to
match what its report shows: all severities, mm, no refill, and an empty
`schematic_parity` array. A second run with `--schematic-parity` gives the same 22
violations plus 33 parity notices (below); that run differs from the original only in
the parity array, which confirms the original ran without the parity check.

## Where the thresholds come from

`board-p-COUT1206-TRIAL.kicad_pro` is 89 bytes of metadata and the PCB `setup` block
only sets `pad_to_mask_clearance 0`. No `.kicad_dru` exists. So **0.200 mm clearance
and 0.250 mm hole clearance are KiCad's built-in defaults**, not a sourced JLCPCB
capability rule set. The candidate has no project design rules at all (net classes,
minimum track/via, mask web). That gap is separate from the 22 findings and still open.

## Classification

Categories: **G** = resolvable by geometry change; **A** = covered by the V197-recorded
user-accepted process assumption; **W** = needs a waiver that needs explicit approval.

### U1 HUSB238 DFN10 — 18 × clearance 0.1500 mm vs 0.2000 mm

Footprint `husb-candidate:HUSB238_DFN10_3x3_EP1.7x2.4_PASTE_PROPOSAL` is an engineered
draft from the Rev2.5 p13 outline, not a manufacturer land pattern. Signal pads are
0.80 × 0.35 mm at x = ±1.40, pitch 0.50; EP is 1.70 × 2.40 mm; mask margin 0.020 mm.

| Findings | Exact cause | G | A | W |
| --- | --- | --- | --- | --- |
| 8 neighbour pairs 1–2, 2–3, 3–4, 4–5, 6–7, 7–8, 8–9, 9–10 | 0.50 pitch − 0.35 pad width = 0.150 copper gap; mask web 0.150 − 2 × 0.020 = 0.110 mm | Only by a land change (pad width ≤ 0.30 mm). Routing cannot fix it | **Yes**: U1 0.150 copper / 0.110 nominal mask web | Not needed beyond A |
| 10 pad-to-EP pairs 1–11 … 10–11 | Pad inner edge at 1.40 − 0.40 = 1.00 mm; EP half-width 0.85 mm → 0.150 gap; every pad's y-span overlaps the EP's ±1.20 | Only by a land change (EP copper ≤ 1.60 mm wide, or pads shortened inward by 0.05 mm) | **Yes** | Not needed beyond A |

Disposition: **A**. A land change would only satisfy a generic default and is not
recommended. The acceptance covers proceeding on feasibility; it is not a supplier
guarantee of finished mask dams, stencil release or yield.

### J1 GCT USB4105 printed land pattern — 4 × hole_clearance vs 0.2500 mm

Signal-row lands are rectangles 0.60 × 1.15 mm at y = 7.355 (spanning y 6.78–7.93);
the two Ø0.65 mm NPTH locating holes sit at (10.61, 6.28) and (16.39, 6.28).

| Finding | Exact cause | G (minimum trim) | A | W |
| --- | --- | --- | --- | --- |
| A1/B12 GND (16.70) ↔ right NPTH: 0.1751 | Land corner (16.40, 6.78) is 0.5001 mm from the hole centre, minus r 0.325 | Trim the hole-side land end by 0.025 mm to reach 0.20, or 0.075 mm to reach 0.25 (departs from the printed pattern) | Printed pattern accepted | **Yes**: below the retained 0.20 mm NPTH guidance; recorded only as a working assumption |
| B1/A12 GND (10.30) ↔ left NPTH: 0.1751 | Mirror of the above | Same | Same | **Yes**: same |
| A4/B9 RAW (15.90) ↔ right NPTH: 0.2099 | Corner (16.20, 6.78): dx 0.19, dy 0.50 | Trim 0.043 mm to reach 0.25 | **Yes**: above the 0.20 guidance, about 0.010 mm nominal margin | Not needed beyond A |
| B4/A9 RAW (11.10) ↔ left NPTH: 0.2099 | Mirror | Same | **Yes** | Not needed beyond A |

Disposition: RAW pair **A**. GND pair is **A for proceeding**, plus an explicit
**W** at order time, because 0.1751 mm is below the published capability guidance the
project retained. The alternative is the smallest geometric fix: a 0.025 mm hole-side
trim of the A1/B12 and B1/A12 lands. That changes the manufacturer printed pattern
(the earlier V150 shortened-land study was not adopted), so it also needs owner
approval. No change was made.

### Formal closure path (not executed)

The V197 inert rule text encodes exactly these 22 pairs at 0.150 (U1), 0.200 (J1 RAW)
and 0.175 (J1 GND), bound to this PCB hash. Activating it as a project `.kicad_dru`
would make DRC report these pairs as within the accepted assumption. It is a scoped
exception, so it needs an explicit coordinator/owner instruction. A complete sourced
project rule set (above) should be added at the same time. Otherwise one exception
file would sit on top of unsourced defaults.

## Schematic-parity notices (informational, from the `--schematic-parity` run)

- 24 × `footprint_symbol_field_mismatch`: footprints lack the schematic's `LCSC` field.
  The PCB carries a stale `LCSC Part` property instead. All 13 `zudo-led-lamp:R0603`
  parts say `C25803`, and CMON says `C15849` (BOM: C14663). **A BOM/CPL generated from the PCB
  would carry wrong supplier codes.** `BOM-TRIAL.csv` and the schematic hold the
  intended codes. This must be fixed (sync fields from the schematic) before any
  assembly export.
- 9 × `net_conflict`: intentionally unconnected pins (J1 A8/B8, JOUT1.3/.4, U1 SDA/SCL,
  U2 PG/ITIMER, UMON OUTB) carry `unconnected-(…)` nets in the schematic and no net on
  the PCB. These are benign naming notices, not connectivity errors.
