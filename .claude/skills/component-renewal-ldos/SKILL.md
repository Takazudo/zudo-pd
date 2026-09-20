---
name: component-renewal-ldos
description: Use to audit exact renewal power-stage parts LT1963AEQ#PBF C107286, LT3015EQ-12#PBF C666307, their ratings, symbol pin maps, output regulation, thermal limits, and evidence availability.
---

# Renewal power-stage evidence

Run the central validator and read all JSON files in this bundle. Identity,
primary specification, mirrored evidence and bench state are distinct. Facts
marked UNSOURCED cannot certify a quantitative operating envelope. Source URLs
were retrieved on 2026-09-20; stock is not promised by a catalog identity.

## Pin and land-pattern checks

LT1963A Q: pins 1 SHDN, 2 IN, 3 GND, 4 OUT, 5 ADJ; tab is GND.
LT3015 Q: pins 1 SHDN, 2 GND, 3 IN, 4 SENSE, 5 OUT; tab is IN.
The LT3015 imported symbol reversed the functions of pins 1/5 and 2/4.
Use the corrected project symbol and manufacturer drawing; never restore the
uncorrected import. Both footprints represent the tab as pad 6.

Both exact Q parts use drawing 05-08-1461 Rev F. Canonical land dimensions
are converted directly from its plain recommended-pad figure. Leads point
along local +X and pad 1 lies at +Y. The 3D asset is illustrative; copper and
pin assignment are verified against the drawing independently.

## Human component reference

[LT1963AEQ#PBF](/docs/components/records/c107286/), [LT3015EQ-12#PBF](/docs/components/records/c666307/). See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). These pages are generated
from the JSON bundle, which remains authoritative.
