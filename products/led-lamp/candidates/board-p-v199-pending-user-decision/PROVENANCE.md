# V199 Board P scratch candidate (PENDING USER DECISION, UNADOPTED)

**Status: PENDING-USER-DECISION / UNADOPTED.** This is a scratch engineering
candidate built from V198 using the options recommended in
`../board-p-v196-unadopted/FAILOFF-WINDOW.md` and `DRC-CLASSIFICATION.md`. Every one of
those options is still a user decision. It is an unvalidated draft and is not order-ready.
No fabrication or assembly output exists, and none may be produced from it.

Parent: `../board-p-v198-unadopted/`. Every file here is rebuilt from the V198 files by
`tools/build_v199.py`, using one named change per option. Rebuilding with `--skip NAME`
drops that option. Git revert cannot do this, because the PCB keeps all footprints on
one line and the commits touch the same line.

| Change (`--skip` name) | What | Decision it waits on |
| --- | --- | --- |
| `rmh2-187k` | RMH2 value: 180k → 187k 0.1 % (RT0603BRD07187KL). Same land and same footprint ID. LCSC is left empty because no code is verified | O3 and the RAW ≥ 14.0 V LED-first scope |
| `cout-datasheet` | Adds the COUT `Datasheet` property to the PCB footprint, copied from the schematic URL. This clears the one V198 field-parity notice | None; this is a field sync |
| `j1-gnd-trim` | J1 A1/B12 and B1/A12 GND lands are shortened 0.025 mm at the end facing the Ø0.65 mm NPTH: length 1.15 → 1.125 mm, centre moved 0.0125 mm away from the hole. Applied to both the PCB and the candidate library footprint. The nominal hole-to-land distance goes 0.1751 → 0.2001 mm | The J1 GND choice: waiver or trim. This departs from the printed GCT land pattern |
| `tvs` | Adds input TVS `DTVS` = SMAJ20A / C571370 (owner record `component-high-diode-smaj20a-c571370`). It uses the retained `SMA_L4.2-W2.6-LS5.3-RD` footprint: pad 1 is the cathode on RAW_USB_VBUS and pad 2 the anode on GND. It is placed at (5.6, 10.87) with rotation −90, left of J1 and below MH1. Routing: a 0.6 mm F.Cu track from the J1 VBUS via square at (11.2, 4.7), and a 0.6 mm F.Cu GND stub to the x = 8 GND track. Also adds the schematic symbol with global labels, the lib-symbol cache entry, the candidate library footprint copy and a BOM row | Adding an input TVS (layout change). The SMAJ20A clamp of 32.4 V is above U2's 28 V abs max |

Checks on the builder:

- Rebuilding with every change skipped reproduces V198 byte-for-byte (PCB, SCH, BOM).
- Each single `--skip` variant builds.
- A full rebuild reproduces the committed files.

## Identity

| File | V198 SHA256 | V199 SHA256 |
| --- | --- | --- |
| `board-p-COUT1206-TRIAL.kicad_pcb` | `762ff264…6a8b2` | `b279b8d02e8c1ee3f6000ca4cc744d1066eeaccd124db4a1e9bbd86653bd1297` |
| `board-p-COUT1206-TRIAL.kicad_sch` | `373bb8d3…7b167b` | `c83d30199645f76d3ca869cf20440b44fd0b957e951c304dd7414b21bc34e4c9` |
| `BOM-TRIAL.csv` | `e9b19387…61b45` | `b2c09ccee8e2f09659bb588d0e8eda03fa9ae2c9ab33628ace6f3fe9d45d3e78` |
| `libraries/trial.pretty/USB4105_V106_TRIAL_UNASSIGNED.kicad_mod` | V198 copy | `7b5e6e2b501f984f794e7d4389d263a333d2947403d528ae1db0259441e3c518` (trimmed) |
| `libraries/zudo-led-lamp.pretty/SMA_L4.2-W2.6-LS5.3-RD.kicad_mod` | — | `1cdb4a8a90c33fd3506c829d46dafe539e2b5753e10528c672776d8baa9efba4` (copy of `footprints/kicad/zudo-led-lamp.pretty/`) |

## Native DRC with default rules (2026-10-31): FAIL (exit 5), 22 findings, same set as V198

Run setup: pinned image `kicad/kicad@sha256:18693567…dd3ec`, `kicad-cli` 10.0.6,
`--network none`, 2 CPU / 6 GB, `flock /tmp/kicad-native.lock`, no zone fill. It ran on a
scratch copy whose PCB, SCH and libraries match these committed files. The command is in
`evidence/native-20261031/COMMAND.txt`.

| Run | Exit | Violations | Unconnected | Parity |
| --- | --- | --- | --- | --- |
| No parity (`V199-drc.json`, SHA256 `8d1be671…d4a2`) | 5 | 22 | 0 | — |
| With parity (`V199-drc-with-parity.json`, SHA256 `da2c6ba7…f6fd`) | 5 | 22 | 0 | 10 |

**Delta vs V198**

- Each of the 22 findings is the same item pair as in V198.
- Two findings changed value: the J1 GND ↔ NPTH `hole_clearance` pairs went from
  0.1751 mm to **0.2001 mm**. They are still below KiCad's default 0.250 mm hole clearance,
  so they still appear.
- Adding DTVS and its routing **introduced no new violation and no unconnected item**.
- RMH2 is a value-only change.
- Parity notices:
  - The COUT `Datasheet` notice is gone.
  - KiCad now reports the next COUT field difference, `Description`: empty on the PCB,
    while the schematic text says "UNADOPTED COUT-only …". This is left for the next field
    revision, so this file set stays the one that was checked.
  - The 9 benign NC-name `net_conflict` notices are unchanged.
  - DTVS raises no parity notice.

## Scratch DRC with the UNAPPLIED base rules: informational, 0 findings

The rule text `../board-p-v196-unadopted/rules/UNAPPLIED-base-rules-jlc.kicad_dru.txt`
(SHA256 `952177c6…b3a3`) was copied as `board-p-COUT1206-TRIAL.kicad_dru` **into a
separate scratch copy only**. No `.kicad_dru` exists in this or any committed candidate.
The same oracle and limits were used. Result: exit 0, **0 violations, 0 unconnected**
(`evidence/scratch-baserules-20261031/`, SHA256 `d836a2d3…f6fd`).

The rule file was in effect. Without it, the U1 0.150 mm pad pairs and the J1 RAW 0.2099 mm
hole pairs are flagged under the defaults; with it, they pass.

Read the zero carefully:

- The U1 pairs sit exactly on the published 0.15 mm SMD pad-to-pad capability.
- J1 RAW (0.2099 mm) and the trimmed J1 GND (0.2001 mm) clear the 0.20 mm NPTH row by only
  0.0099 mm and 0.0001 mm nominal. Both are far inside the ±0.075 mm hole-position
  tolerance.
- None of this is a DRC pass for order purposes. It is a proposal check only.

## Known limitations of this scratch layout

- **DTVS:**
  - Its path to the J1 pins is about 10 mm long and runs through the existing 4-via VBUS
    square. Its GND return is a 0.25 mm track, not a plane. Clamp effectiveness at
    hot-plug is unmeasured.
  - The retained SMA footprint's courtyard (4.2 × 2.6 mm) does not enclose its pads. This
    is an inherited asset property and is not changed here.
- **SMAJ20A clamp:** its VC of 32.4 V at 12.3 A is above U2's 28 V abs max. It bounds the
  energy but does not guarantee U2 survival (see `FAILOFF-WINDOW.md`).
- **RMH2:** the footprint ID still says 180KL, and only the value, MPN and BOM changed. A
  verified LCSC code is still missing.
