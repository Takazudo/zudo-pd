# V196 BOM reconciliation (desk record, no live sourcing)

Basis: `BOM-TRIAL.csv` and the PCB of this directory (V196), compared with:

- the old remote HUSB006 snapshot `codex/husb006-native-verification` @ `3d49db76`,
  `verification/husb006/installed-bom.csv`;
- the V15 isolated packet `two-board-installed-bom.csv` (handoff supplemental source
  archive).

No price, stock, MOQ or assembly-eligibility data was refreshed. Installed demand is
not purchase quantity.

## Counts reconcile once the differences are named

| Source | Footprints / placements | Pads | Orderable lines | Notes |
| --- | --- | --- | --- | --- |
| Old remote `3d49db76` | 20 placements | — (schematic only) | 20 | No TPS3701 monitor; J1 = TYPE-C-31-M-17 C283540; COUT = 0603 1 µF |
| V15 packet | 25 placements | — (schematic only) | 20 | +UMON, RMH1, RMH2, RML, CMON; J1 = TYPE-C-31-M-12 C165948 (footprint blank); COUT and C1 share CL10A105KB8NNNC |
| **V196 (this candidate)** | **27 footprints = 25 BOM placements + MH1/MH2** | **106** | **21** | COUT → CL31B475KBHNNNE 1206 4.7 µF (C51205), now its own line; J1 → GCT USB4105 printed pattern, **MPN/LCSC blank** |

The 106 pads include 4 U1 paste-only apertures, 8 U2 paste-only apertures, 4 J1 shell
THT pads, 2 J1 NPTH and 2 board NPTH. MH1/MH2 are `board_only exclude_from_bom
exclude_from_pos_files` and need no purchase.

V15 → V196 delta: same 25 references and nets. COUT changed part (0603 1 µF →
1206 4.7 µF X7R), and J1 changed connector family (HRO M-12 → GCT USB4105). M-12 is
not the V196 connector, and the old M-17 / STUSB parts are not restored.

## Per-line demand for two lamps (V196)

| # | MPN | LCSC | Refs | Per board | 2 boards |
| --- | --- | --- | --- | --- | --- |
| 1 | CL10A105KB8NNNC | C15849 | C1 | 1 | 2 |
| 2 | CC0603KRX7R9BB104 | C14663 | CMON | 1 | 2 |
| 3 | CL31B475KBHNNNE | C51205 | COUT | 1 | 2 |
| 4 | GRM21B5C1H223JA01L | C77069 | CSLEW | 1 | 2 |
| 5 | **USB4105 (exact suffix open)** | **none recorded** | J1 | 1 | 2 |
| 6 | PZ254V-11-06P | C492405 | JOUT1 | 1 | 2 |
| 7 | SMMBT3904LT1G | C84555 | QINH | 1 | 2 |
| 8 | RT0603BRD07100KL | C122538 | RB, RG | 2 | 4 |
| 9 | RC0603FR-071ML | C105578 | RBE | 1 | 2 |
| 10 | 1210W2F2201T5E | C422361 | RBLEED | 1 | 2 |
| 11 | RC0603FR-071K27L | C245930 | RILM | 1 | 2 |
| 12 | 0603WAF2262T5E | C22959 | RISET | 1 | 2 |
| 13 | RT0603BRD07133KL | C861111 | RMH1, ROVH | 2 | 4 |
| 14 | RT0603BRD07180KL | C326731 | RMH2 | 1 | 2 |
| 15 | RT0603BRD0710KL | C95204 | RML, ROVL, RUVL | 3 | 6 |
| 16 | 0603WAF1000T5E | C22775 | RSLEW | 1 | 2 |
| 17 | RT0603BRD0797K6L | C861608 | RUVH | 1 | 2 |
| 18 | 0603WAF1402T5E | C22803 | RVSET | 1 | 2 |
| 19 | HUSB238_006DD | C55013903 | U1 | 1 | 2 |
| 20 | TPS259474LRPWR | C2864845 | U2 | 1 | 2 |
| 21 | TPS3701DDCT | C132027 | UMON | 1 | 2 |
| | **Total** | | | **25** | **50** |

## The four quantities, kept separate

| Quantity | Value | Status |
| --- | --- | --- |
| Required placements | 25 per Board P, 50 for two finished lamps (plus 2 bare-PCB NPTH features each) | Derived from V196 |
| New purchases | All 21 lines for Board P. No existing Board P inventory is reusable: the two 2026-09-19 STUSB4500 Board Ps are a different design, and rework is not authorized | Purchase quantity UNSET; J1 orderable missing |
| MOQ / surplus | UNKNOWN for every line: JLC part MOQ, attrition, Extended-part fees and PCB/PCBA minimum board quantity were not checked. The only retained commercial observation is for M-12 C165948 (2026-10-23, MOQ 1), which is not the V196 J1 | Needs a dated sourcing pass at order preparation |
| Reuse | Board L: 2 existing assembled boards for 2 lamps, 0 new Board L builds (user decision). Health, factory programming and as-built revision of those boards are not established | Reuse planned, not qualified |

## Findings that block a reproducible BOM/CPL

1. **J1 has no MPN/LCSC code.** CAD evidence names USB4105-GF-A, but its geometry
   comes from the USB4105-15-A model (a plating-only family bridge, not accepted). The
   exact orderable and its JLC availability/assembly route are open.
2. **The PCB footprint `LCSC Part` properties are stale.** All 13 `R0603` footprints
   carry `C25803`, and CMON carries `C15849`. U1, U2, UMON, QINH, CSLEW, RBLEED and J1
   carry none. A BOM/CPL generated from the PCB would be wrong. Sync footprint fields
   from the schematic (24 parity notices) before any export.
3. V196 has no CPL, Gerber or drill outputs, and none may be made without approval.
   Orientation and pin-1 rotation for U1, U2, UMON and QINH are unverified.
