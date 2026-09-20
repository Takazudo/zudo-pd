---
name: component-hdr-2541wr-2x08p-c5383092
description: Audit the exact board-b 2x8 Eurorack power headers J10/J11 (project value 2541WR-2X08P, LCSC C5383092, HanElectricity 16-pin dual-row THT header, footprint HDR-TH_16P-P2.54-H-M-R2-C8-S2.54). Use for pin-pair rail assignment, GND moat, current rating per contact vs the rail budgets, PCB hole fit, or the not-netlist-verifiable key/polarization orientation.
---

# HanElectricity 2541WR-2X08P (LCSC C5383092) — retired

Historical v0.4.0 evidence only. The renewal replaces J10/J11 with DEALON
DW254P-2X8-L0 C4749189 under its own owner skill and conventional pin1/2=-12V
assignment. Numeric pin groups below describe the retired part, not the new PCB.

Run the central validator and read every local artifact. LCSC catalogs C5383092 as
manufacturer HanElectricity, model `2541WR-2x08P` (distributor renders lowercase x; the
project inventories uppercase `2541WR-2X08P` -- a formatting variance, not an identity
conflict), matching the v0.4.0 as-ordered BOM row for J10/J11. The manufacturer's own
engineering drawing is a **generic-family** drawing (part number literally `2541WR-2xXXP`)
covering the whole 2xNN position-count family, so every electrical rating pulled from it
(250V/3.0A AC/DC, -40 to +105 C) is a family-level figure, not confirmed specifically for
this 16-position/2x8 variant; no independently-reachable manufacturer-primary source was
checked beyond the LCSC-hosted drawing mirror, so every rating stays UNSOURCED.

Pin pairs (per board-b-synth-power.md, doc-level only): 1-2 GATE (isolated stub), 3-4 CV
(isolated stub), 5-6 +5V, 7-8 +12V, 9-14 GND (six-pin moat separating +12V from -12V),
15-16 -12V. This table is **not** promoted into the Ref.Pin-granularity
`scripts/schgen/baselines/board-b.json` baseline -- it explicitly lists GATE rail, CV
rail, and GND(output stage) as unresolved for J10/J11 because J10 vs J11 physical-pin
identity is not disambiguated in the source doc. The 2x8 shrouded key/polarization-slot
orientation (which physical pin is "pin 1") is a standing NEEDS BENCH checklist item --
not verifiable from the netlist or any KiCad asset, confirm against the footprint
silkscreen or a physical board before Board B layout is finalized.

## Human component reference

The retired record remains in this local evidence bundle as a rejected candidate;
it has no current public component page. See the
[current socket record](/docs/components/records/dealon-dw254p-2x8-l0-c4749189/),
[component catalog](/docs/components/catalog/), and
[cross-component rules](/docs/components/integration/).
