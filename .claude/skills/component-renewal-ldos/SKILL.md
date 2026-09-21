---
name: component-renewal-ldos
description: Use to audit exact renewal power-stage parts LT1963AEQ#TRPBF C459702, LT3015EQ#PBF C666306, their ratings, symbol pin maps, output regulation, thermal limits, and evidence availability.
---

# Renewal power-stage evidence

Run the central validator and read all JSON files in this bundle. Identity,
primary specification, mirrored evidence and bench state are distinct. Facts
marked UNSOURCED cannot certify a quantitative operating envelope. Source URLs
were retrieved on 2026-09-20; stock is not promised by a catalog identity.
On 2026-09-21 LT1963AEQ#PBF C107286 and every fixed -12 V LT3015 orderable were
out of stock at JLCPCB. The same-die tape-and-reel LT1963AEQ#TRPBF C459702 and
the adjustable LT3015EQ#PBF C666306 replaced them; both datasheet mirrors are
byte-identical to the previously locked files.

## Pin and land-pattern checks

LT1963A Q: pins 1 SHDN, 2 IN, 3 GND, 4 OUT, 5 ADJ; tab is GND.
LT3015 Q (adjustable LT3015EQ#PBF): pins 1 SHDN, 2 GND, 3 IN, 4 ADJ, 5 OUT; tab is IN.
Pin 4 is SENSE only on fixed-voltage versions. U8 is programmed by R26 8.2 k +
R27 680 R from OUT to ADJ over R28 1 k from ADJ to ground: nominal -12.054 V.
The -1.196 to -1.244 V reference band is full-temperature; the +/-200 nA ADJ
bias limit is 25 C only. Do not drive ADJ more than 0.3 V below IN.
The LT3015 imported symbol reversed the functions of pins 1/5 and 2/4.
Use the corrected project symbol and manufacturer drawing; never restore the
uncorrected import. Both footprints represent the tab as pad 6.

Both exact Q parts use drawing 05-08-1461 Rev F. Canonical land dimensions
are converted directly from its plain recommended-pad figure. Leads point
along local +X and pad 1 lies at +Y. The 3D asset is illustrative; copper and
pin assignment are verified against the drawing independently.

## Human component reference

[LT1963AEQ#TRPBF](/docs/components/records/c459702/), [LT3015EQ#PBF](/docs/components/records/c666306/). See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). These pages are generated
from the JSON bundle, which remains authoritative.
