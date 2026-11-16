# Design-rule texts for the V196/V198 candidates — all UNAPPLIED

No file in this directory is an active KiCad rule file. There is no `.kicad_dru` in the
candidate projects, and none may be created from these texts without an explicit
coordinator or owner instruction naming the target revision. Until then, native DRC runs
against KiCad's built-in defaults (0.200 mm clearance, 0.250 mm hole clearance), as
recorded in `../DRC-CLASSIFICATION.md`.

| File | What it is | Bound to |
| --- | --- | --- |
| `UNAPPLIED-base-rules-jlc.kicad_dru.txt` | Proposed base rule set derived from JLCPCB's public PCB capability page | Generic 2-layer 1 oz board; not hash-bound |
| `v197-inert/UNAPPLIED-rules.kicad_dru.txt` + `UNAPPLIED-CONTRACT.json`, `SELECTORS.json`, `SOURCE-BINDINGS.json`, `MANIFEST.json` | V197 exact-feature rules for the 22 known findings; copied byte-for-byte from the V197 packet (4/4 manifest hashes match) | V196 PCB `c191997b…` only. **Stale for V198**: its exact-input preflight rejects any other PCB hash |

## Base-rule source

JLCPCB "PCB Capabilities", https://jlcpcb.com/capabilities/pcb-capabilities, retrieved
2026-10-31 with one ordinary GET. HTML SHA256
`c84e91a3d7c42dbd5561d017e1e65c8dec58b028315475cba606b1a989c1f850` (139,273 B). The page is
dynamic; the values below are what it stated on that date.

| Rule | Published row | Value | Proposed constraint |
| --- | --- | --- | --- |
| Track width | Min. track width and spacing (1 oz), 2-layer | 0.10 / 0.10 mm | track_width ≥ 0.10 |
| General clearance | (project margin, not JLC) | — | clearance ≥ 0.20 |
| SMD pad to pad, different nets | SMD pad to pad clearance | 0.15 mm | clearance ≥ 0.15 for SMD–SMD pads |
| Mask bridge | Soldermask bridge, 1 oz green | min pad spacing 0.10 mm | covered by the 0.15 pad rule |
| Via | Min. via hole size/diameter, 2-layer | 0.15 / 0.25 mm; diameter ≥ hole + 0.10 | hole ≥ 0.15, diameter ≥ 0.25, annular ≥ 0.05 |
| PTH pad annular | PTH annular ring, 2-layer 1 oz | rec 0.25, abs min 0.18 mm | annular ≥ 0.18 |
| NPTH | Min. non-plated holes | 0.50 mm | hole ≥ 0.50 |
| Hole to hole | Via hole-to-hole / pad hole-to-hole | 0.20 / 0.45 mm | as stated |
| Copper to hole | Via hole to track / NPTH to track | 0.20 mm | hole_clearance ≥ 0.20 |
| Copper to PTH | PTH to track | min 0.28, rec 0.35 mm | hole_clearance ≥ 0.28 near plated THT holes |
| Board edge | Copper clearance from routed edges | ≥ 0.2 mm | edge_clearance ≥ 0.20 |
| Hole position | Hole position tolerance | ±0.075 mm | not a DRC constraint; see below |

## Predicted effect on the 22 known findings (desk prediction, NOT RUN)

- **U1, 18 × 0.150 mm:** these would meet the published SMD pad-to-pad capability of
  0.15 mm exactly, with zero margin, and the bridge capability of 0.10 mm. The V197
  user-accepted assumption stays the authority. The sourced row shows the assumption
  sits at, not beyond, the published limit.
- **J1 RAW, 2 × 0.2099 mm:** these would meet the 0.20 mm NPTH-to-copper row. The
  nominal margin, 0.0099 mm, is far smaller than the ±0.075 mm hole-position tolerance.
- **J1 GND, 2 × 0.1751 mm:** these would still **fail** the 0.20 mm row. This remains the
  pending owner decision: an explicit waiver, or the 0.025 mm land trim.
- Other new findings from the added rules (annular, hole-to-hole, edge) are unknown.
  The rule syntax and its native evaluation are **NOT RUN**, because evaluating requires
  activating the file. A scratch-copy evaluation is the first step once activation is
  authorised.

Applying this base set does not by itself make the board order-ready. It replaces
unsourced defaults with sourced minimums. Margins above those minimums are project
choices recorded as such.
